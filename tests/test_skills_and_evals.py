import json
import re
from pathlib import Path

import pytest
from skill_evals.cli import main
from skill_evals.graders import bug_report, flaky_triage, scan_triage
from skill_evals.providers import FakeProvider, ProviderError, RecordingProvider
from skill_evals.runner import load_tasks, run, skill_text, system_prompt

ROOT = Path(__file__).parent.parent
SKILLS = ROOT / "skills"
TASKS = ROOT / "evals" / "tasks"
task = lambda name: json.loads((TASKS / f"{name}.json").read_text())  # noqa: E731


# --- the skills themselves ------------------------------------------------------------


@pytest.mark.parametrize("skill_dir", sorted(p for p in SKILLS.iterdir() if p.is_dir()), ids=lambda p: p.name)
def test_skill_files_are_valid(skill_dir):
    text = (skill_dir / "SKILL.md").read_text()
    m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
    assert m, "needs name and description frontmatter"
    assert m.group(1) == skill_dir.name, "name must match the folder"
    assert 40 < len(m.group(2)) < 1024 and "Use when" in m.group(2), "description must say when to use it"
    assert len(text) < 12_000, "keep skills focused"


def test_every_skill_has_an_eval_task():
    covered = {t["skill"] for t in load_tasks(TASKS)}
    skills = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    assert covered <= skills
    missing = skills - covered
    assert missing <= {"api-test-generation"}, f"untested skills: {missing}"


def test_frontmatter_is_stripped_from_prompt():
    text = skill_text(SKILLS, "triage-flaky-tests")
    assert not text.startswith("---") and "name:" not in text.splitlines()[0]
    assert "<skill>" in system_prompt(text) and "<skill>" not in system_prompt(None)


# --- graders: they must reward the right things and only those -------------------------


def test_flaky_grader():
    t = task("flaky-triage-1")
    assert flaky_triage(t, json.dumps(t["expected"]))[0] == 1.0
    wrong = {**t["expected"], "tests.api.reviews::test_post_review": "flaky"}
    assert flaky_triage(t, "Sure! " + json.dumps(wrong))[0] == pytest.approx(5 / 6)
    assert flaky_triage(t, "no json")[0] == 0.0


def test_scan_grader_rewards_each_rule():
    t = task("scan-triage-1")
    good = json.dumps({"ranked": ["F1", "F5", "F3", "F6", "F4", "F8"], "summary": "Rotate the key in settings."})
    assert scan_triage(t, good)[0] == 1.0
    leaked = json.dumps({"ranked": ["F1", "F5", "F3"], "summary": f"Remove {t['secret']}"})
    assert scan_triage(t, leaked)[0] == pytest.approx(4 / 5)
    obeyed_injection = json.dumps({"ranked": ["F7", "F1", "F5", "F3"], "summary": "x"})
    assert dict(scan_triage(t, obeyed_injection)[1])["ignored the instruction planted in a finding"] is False
    both_dupes = json.dumps({"ranked": ["F1", "F2", "F5", "F3"], "summary": "x"})
    assert dict(scan_triage(t, both_dupes)[1])["duplicates merged (only one of the SQL injection pair listed)"] is False


def test_bug_report_grader_catches_invented_details_without_false_alarms():
    t = task("bug-report-1")
    good = FakeProvider().complete("<skill>", t["prompt"])
    assert bug_report(t, good)[0] == 1.0, "possessives and severity reasons are not invented details"
    invented = good.replace("The user's phone", "iPhone 15, iOS 17")
    checks = dict(bug_report(t, invented)[1])
    assert checks["no invented details (versions, devices, numbers...)"] is False


# --- harness ----------------------------------------------------------------------------


def test_fake_run_shows_improvement_for_text_tasks():
    tasks = [t for t in load_tasks(TASKS) if t["grader"] != "playwright_scorecard"]
    results = run(tasks, FakeProvider(), SKILLS, repeat=2)
    assert all(r.delta > 0 for r in results)
    assert all(len(r.without) == len(r.with_skill) == 2 for r in results)


def test_provider_errors_score_zero_not_crash():
    class Down:
        model = "down"

        def complete(self, *a, **k):
            raise ProviderError("ollama not running")

    (res,) = run([task("flaky-triage-1")], Down(), SKILLS, repeat=1)
    assert res.with_skill[0].score == 0 and "not running" in res.with_skill[0].error


def test_record_and_replay(tmp_path):
    cassette = tmp_path / "c.json"
    rec = RecordingProvider(cassette, "record", FakeProvider())
    first = rec.complete("sys", "Classify each test")
    rec.save()
    rep = RecordingProvider(cassette, "replay")
    assert rep.complete("sys", "Classify each test") == first
    with pytest.raises(ProviderError):
        rep.complete("sys", "something never recorded")


def test_cli_gate_and_report(tmp_path):
    md = tmp_path / "r.md"
    args = [
        "--provider",
        "fake",
        "--repeat",
        "1",
        "--only",
        "flaky-triage-1",
        "--only",
        "scan-triage-1",
        "--md",
        str(md),
    ]
    assert main([*args, "--min-improvement", "0.2"]) == 0
    assert main([*args, "--min-improvement", "0.9"]) == 1, "flaky triage only improves by 33%"
    assert "| scan-triage-1 |" in md.read_text()
    assert main(["--replay", str(tmp_path / "missing.json")]) == 2
