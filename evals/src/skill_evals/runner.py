"""Run each task with and without its skill, several times, and compare the scores."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from skill_evals.graders import GRADERS
from skill_evals.providers import ProviderError

BASE_SYSTEM = "You are a careful senior QA engineer. Follow the user's output format exactly."


def system_prompt(skill_text: str | None) -> str:
    if not skill_text:
        return BASE_SYSTEM
    return f"{BASE_SYSTEM}\n\nUse this skill:\n<skill>\n{skill_text}\n</skill>"


@dataclass
class Trial:
    score: float
    checks: list[tuple[str, bool]]
    error: str = ""


@dataclass
class TaskResult:
    task_id: str
    skill: str
    without: list[Trial] = field(default_factory=list)
    with_skill: list[Trial] = field(default_factory=list)

    @staticmethod
    def mean(trials: list[Trial]) -> float:
        return statistics.mean(t.score for t in trials) if trials else 0.0

    @property
    def delta(self) -> float:
        return self.mean(self.with_skill) - self.mean(self.without)


def load_tasks(tasks_dir: str | Path, only: list[str] | None = None) -> list[dict]:
    tasks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(tasks_dir).glob("*.json"))]
    return [t for t in tasks if not only or t["id"] in only or t["skill"] in only]


def skill_text(skills_dir: str | Path, name: str) -> str:
    path = Path(skills_dir) / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    return text.split("---", 2)[2].strip() if text.startswith("---") else text  # drop frontmatter


def run(tasks: list[dict], provider, skills_dir: str | Path, repeat: int = 3, log=lambda _: None) -> list[TaskResult]:
    results = []
    for task in tasks:
        grade = GRADERS[task["grader"]]
        res = TaskResult(task["id"], task["skill"])
        for label, trials, text in (
            ("without", res.without, None),
            ("with", res.with_skill, skill_text(skills_dir, task["skill"])),
        ):
            for i in range(repeat):
                try:
                    output = provider.complete(system_prompt(text), task["prompt"])
                    score, checks = grade(task, output)
                    trials.append(Trial(score, checks))
                except ProviderError as exc:
                    trials.append(Trial(0.0, [], str(exc)))
                log(f"{task['id']:<20} {label:<7} run {i + 1}: {trials[-1].score:.0%}")
        results.append(res)
    return results


def markdown(results: list[TaskResult], model: str, repeat: int) -> str:
    lines = [
        "## 🧪 Skill evaluation",
        "",
        f"Model `{model}` · {repeat} runs per condition · scores from deterministic graders (code, not an AI judge)",
        "",
        "| Task | Skill | Without skill | With skill | Change |",
        "|---|---|--:|--:|--:|",
    ]
    for r in results:
        d = r.delta
        arrow = "🟢" if d > 0.05 else "🔴" if d < -0.05 else "⚪"
        lines.append(
            f"| {r.task_id} | `{r.skill}` | {r.mean(r.without):.0%} | {r.mean(r.with_skill):.0%} | {arrow} {d:+.0%} |"
        )
    lines.append("")
    for r in results:
        lines += [f"<details><summary>{r.task_id}: checks</summary>", "", "| Check | Without | With |", "|---|--:|--:|"]
        names = [c for c, _ in (r.with_skill[0].checks if r.with_skill and r.with_skill[0].checks else [])]
        for i, name in enumerate(names):

            def rate(trials, i=i):
                vals = [t.checks[i][1] for t in trials if len(t.checks) > i]
                return f"{sum(vals)}/{len(vals)}" if vals else "-"

            lines.append(f"| {name.replace('|', '/')} | {rate(r.without)} | {rate(r.with_skill)} |")
        errors = [t.error for t in r.without + r.with_skill if t.error]
        if errors:
            lines += ["", f"Errors: {errors[0]}"]
        lines += ["", "</details>", ""]
    return "\n".join(lines)
