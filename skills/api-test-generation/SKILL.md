---
name: api-test-generation
description: Generate API tests from an OpenAPI spec that are verified against a running API and never encode bugs as expected behavior. Use when asked to write, generate or expand tests for a REST/JSON API.
---

# Generating API tests safely

Generated tests fail in predictable ways: invented endpoints, guessed values, tests that
pass by luck, and tests that quietly lock in bugs. Follow these guardrails.

## 1. Stay inside the spec

- Only call operations, parameters and status codes the spec documents.
- If you believe the spec is wrong or incomplete, say so. Don't test around it.
- Assert only values you can derive from the spec or the data you created. Don't guess.

## 2. Cover each operation systematically

For each operation, propose tests for:
- the happy path, asserting fields as well as the status
- every documented limit: exactly at min and max, and one past each
- invalid types and formats (`"abc"` for a number, `1.5` for an integer, bad emails)
- missing required fields, one at a time
- every documented error status (400, 404, 409...)
- rules stated in summaries ("case-insensitive", "one per email", "returns 500 for X")

Use unique values (`{{unique_email}}`) for anything that must not collide between runs.

## 3. Verify before keeping

- Run every proposed test against a **known-good** build of the API, 3 times.
- Passes 3/3: keep it. Mixed results: drop it as flaky. Fails 3/3: **flag it for human
  review**: it is either a wrong expectation or a real bug.
- **Never rewrite an expectation to match what the API returned.** If the API is wrong,
  that turns the bug into a passing test. This is the most important rule here.
- Generating against a buggy build is dangerous: a wrong guess can pass because the bug
  agrees with it. Use a build you trust.

## 4. Prefer data over code

Describe tests as data (method, path, query, body, expected status, expected fields) and
render them with a fixed template. Reviewers can read data at a glance, and nothing you
write gets executed as arbitrary code.

## 5. Measure, don't count

Test count means nothing. If one-bug copies of the API exist (mutants), run the kept tests
against each: a mutant that survives is a gap. Report which ones and suggest the missing test.

If `testgen-agent` is available it implements all of the above:

```bash
pip install git+https://github.com/Kurtis-H/testgen-agent
testgen --spec openapi.json --base-url http://localhost:3000 --mutant NAME=URL
```
