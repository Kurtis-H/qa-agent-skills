---
name: test-and-report-on-pr
description: Test the changes in a pull request end to end - derive test cases from the diff, run them with Playwright, capture screenshots, traces and video of failures, and post a clear report on the PR. Use when asked to QA, test or verify a pull request or branch.
---

# Testing a pull request and reporting on it

The goal is a PR comment a developer can act on in two minutes: what was tested, what
broke, how to reproduce it, and proof.

## 1. Work out what changed

- Read the diff (`git diff origin/main...HEAD`) and the PR description.
- List every user-visible behavior the change touches: pages, API endpoints, validation
  rules, calculations, permissions. Include behavior near the change that could be
  affected (the same form, the same table, the same endpoint's other methods).
- Note what's NOT covered by the change, so the report can say what wasn't tested.

## 2. Turn changes into test cases

For each touched behavior write cases using the `write-playwright-tests` rules:
the happy path, every boundary of every rule, invalid input, the error path, and a
regression check that what used to work still works. Name each case after the behavior
it proves ("discount applies only once"), not the action ("click apply").

## 3. Run with evidence switched on

```ts
// playwright.config.ts
use: {
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
  trace: 'retain-on-failure',
}
```

- Run against the PR's build (a preview deployment or the app started in CI).
- Never retry to make a run green. A test that passes on retry is reported as flaky.
- For each failure, keep: the screenshot, the trace (`npx playwright show-trace`), the
  video, the console errors and any failed network requests.

## 4. Check each failure before reporting it

A failure is either a product bug, a test bug or an environment problem. Before calling
it a bug: reproduce it once by hand or by re-running only that test, and confirm the
expectation is right according to the requirements, not your guess.

## 5. Post the report on the PR

Upload the evidence as a CI artifact (or to the PR), then post ONE comment, updated in
place on each run rather than adding a new comment every time:

```markdown
## 🧪 QA report: <n> passed · <n> failed · <n> flaky

### ❌ Failures
**<behavior that broke>**: <one-line impact>
1. <step>  2. <step>
Expected: <...> · Actual: <...>
📸 [screenshot](<link>) · 🎞️ [trace](<link>) · Console: `<first error>`

### ⚠️ Flaky (passed on re-run, needs a look)
### ✅ Covered
<collapsed list of behaviors tested>
### Not tested
<what the change touches that wasn't covered, and why>
```

Rules for the comment:
- Failures first, then flaky, then passes collapsed in `<details>`.
- Every failure has steps to reproduce, expected vs. actual, and at least one piece of evidence.
- Redact secrets, tokens and personal data from logs and screenshots before posting.
- Don't paste huge logs. Link the artifact instead.
- Say plainly if the run couldn't test something (no test account, service down).

In GitHub Actions, post with `gh pr comment <number> --body-file report.md --edit-last`
(falls back to a new comment the first time), using the built-in `GITHUB_TOKEN`. Free on
public repos.
