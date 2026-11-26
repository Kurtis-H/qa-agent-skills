---
name: test-quality-review
description: Review automated tests for whether they would actually catch bugs - weak assertions, missing edge cases, flakiness risks and tests that can't fail. Use when asked to review, audit or improve tests, or to check test quality in a PR.
---

# Reviewing test quality

The question for every test: **if the feature broke, would this test go red?** Coverage
numbers can't answer that. A test can execute every line and assert nothing useful.

## 1. Problems to look for

| Problem | Looks like | Why it's bad |
|---|---|---|
| **Weak assertion** | only `toBeVisible()`, `status < 500`, `assert result`, `is not None` | passes when the value is wrong |
| **No assertion** | actions with no `expect`/`assert`, or only in a `try` that swallows errors | can't fail |
| **Fixed sleeps** | `waitForTimeout(3000)`, `time.sleep(2)` | slow AND flaky |
| **Retries hiding failures** | `retries: 3`, `@flaky(reruns=5)`, loops until it passes | turns real race conditions green |
| **Happy path only** | no invalid input, no boundary, no error case | misses most real bugs |
| **Missing boundaries** | a rule "at least 8" tested only with 12 | off-by-one bugs pass |
| **Shared or order-dependent state** | tests reuse the same user, or rely on running in order | flaky in parallel |
| **Testing the mock** | asserting the mock returned what it was told to return | proves nothing about the code |
| **Copied expected values** | the expected value computed with the same code under test | the bug is in both sides |
| **Brittle selectors** | long CSS/XPath chains, `nth-child(7)` | break on harmless changes |
| **Unclear name** | `test1`, `it works` | a failure says nothing |

## 2. How to judge "would it fail?"

For each important test, imagine a specific bug: change `>=` to `>`, drop the second
discount check, return an empty list, swap two fields, skip validation. If the test still
passes, it's not protecting that behavior. Real **mutation testing** tools do exactly this
automatically (mutmut for Python, Stryker for JavaScript/TypeScript), and their score is
a far better quality measure than coverage.

## 3. Report

For each problem: file and line (or test name), the problem type from the table, why it
matters, and the fix, ideally the improved assertion itself:

```
cart.spec.ts:12 "cart works" - weak assertion
Only checks the total is visible, so a wrong total passes.
Fix: await expect(page.getByTestId('total')).toHaveText('$99.56');
```

Then list **missing tests**: the behaviors or edge cases nothing covers. These are often
more valuable than fixing existing tests. Don't flag style preferences as quality problems.
