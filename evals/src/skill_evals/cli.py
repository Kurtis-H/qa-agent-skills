"""`skill-evals --provider ollama --model qwen2.5-coder:14b`"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from skill_evals.providers import FakeProvider, OllamaProvider, ProviderError, RecordingProvider
from skill_evals.runner import load_tasks, markdown, run

ROOT = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="skill-evals", description="Score a model on QA tasks with and without each skill."
    )
    p.add_argument("--provider", choices=["ollama", "fake"], default="ollama")
    p.add_argument("--model", default="qwen2.5-coder:14b")
    p.add_argument("--ollama-url", default=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    p.add_argument("--tasks", default=str(ROOT / "evals" / "tasks"))
    p.add_argument("--skills", default=str(ROOT / "skills"))
    p.add_argument("--only", action="append", help="task id or skill name (repeatable)")
    p.add_argument("--repeat", type=int, default=3)
    rec = p.add_mutually_exclusive_group()
    rec.add_argument("--record", metavar="CASSETTE")
    rec.add_argument("--replay", metavar="CASSETTE")
    p.add_argument("--md", help="write the markdown report here")
    p.add_argument("--json", help="write raw results here")
    p.add_argument(
        "--min-improvement", type=float, help="exit 1 if any skill improves its task by less than this (0-1)"
    )
    args = p.parse_args(argv)

    base = FakeProvider() if args.provider == "fake" else OllamaProvider(args.model, args.ollama_url)
    try:
        provider = (RecordingProvider(args.replay, "replay") if args.replay
                    else RecordingProvider(args.record, "record", base) if args.record else base)  # fmt: skip
    except ProviderError as exc:
        print(f"skill-evals: {exc}", file=sys.stderr)
        return 2
    tasks = load_tasks(args.tasks, args.only)
    if not tasks:
        print("skill-evals: no tasks matched", file=sys.stderr)
        return 2

    results = run(tasks, provider, args.skills, args.repeat, log=lambda m: print(m, file=sys.stderr))
    if isinstance(provider, RecordingProvider):
        provider.save()
    model = base.model if not args.replay else "replayed recording"
    report = markdown(results, model, args.repeat)
    if args.md:
        Path(args.md).write_text(report, encoding="utf-8")
        if os.getenv("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
                fh.write(report)
    else:
        print(report)
    if args.json:
        rows = [{"task": r.task_id, "skill": r.skill, "without": r.mean(r.without),
                 "with": r.mean(r.with_skill), "delta": r.delta} for r in results]  # fmt: skip
        Path(args.json).write_text(json.dumps(rows, indent=2))
    if args.min_improvement is not None:
        weak = [r for r in results if r.delta < args.min_improvement]
        for r in weak:
            print(f"skill-evals: {r.skill} improved {r.task_id} by only {r.delta:+.0%}", file=sys.stderr)
        return 1 if weak else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
