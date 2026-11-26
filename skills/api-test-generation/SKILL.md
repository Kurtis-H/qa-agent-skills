---
name: api-test-generation
description: Write or generate API tests - from an OpenAPI spec or by hand - covering contracts, validation, auth, security and concurrency, verified against a running API without ever encoding bugs as expected behavior. Use when asked to test, write tests for, or generate tests for a REST/JSON API.
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

## 5. What every API test suite needs (generated or hand-written)

- **Contract:** response shapes match the spec, and unexpected fields fail the test
  (an extra field can be a data leak, like a password hash).
- **Status codes:** bad input gets 400 or 422, not 200 with an empty body, and not 500.
- **Auth:** no token → 401; a bad or expired token → 401; a valid token for the wrong
  user → 403 or 404. **Test every ID in a URL with another user's token** (broken object-level
  authorization is the most common API vulnerability).
- **Mass assignment:** send fields the client shouldn't control (`"role": "admin"`,
  `"price": 0`) and assert they're ignored.
- **Idempotency:** PUT and DELETE twice give the same result. Retried POSTs with an
  idempotency key don't create duplicates.
- **Concurrency:** fire many simultaneous requests at limited stock (the last seat, a
  one-time code) and assert exactly one succeeds.
- **Pagination:** walk every page; the counts add up; out-of-range pages behave as documented.
- **Rate limits:** if documented, hit them and assert 429 with a retry header.
- **Fuzzing:** property-based tools like Schemathesis throw thousands of generated inputs
  at every endpoint from the spec. Any 500 is a bug.

## 6. Measure, don't count

Test count means nothing. If one-bug copies of the API exist (mutants), run the kept tests
against each: a mutant that survives is a gap. Report which ones and suggest the missing test.

If `testgen-agent` is available it implements all of the above:

```bash
pip install git+https://github.com/Kurtis-H/testgen-agent
testgen --spec openapi.json --base-url http://localhost:3000 --mutant NAME=URL
```
