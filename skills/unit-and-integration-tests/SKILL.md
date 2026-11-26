---
name: unit-and-integration-tests
description: Write developer-side unit and integration tests (pytest, Jest/Vitest, node:test) that pin down behavior at its edges and stay fast and isolated. Use when asked to add tests for a function, module, class, service or endpoint, or when writing new code that needs tests.
---

# Writing unit and integration tests

Unit tests check one piece of logic quickly and exactly. Integration tests check that
pieces work together for real (database, HTTP, file system). You need both, and you
need to know which one you're writing.

## 1. Start from behavior, not code

List what the code promises: inputs and outputs, rules, errors it raises, side effects.
Each promise gets tests. Don't test private helpers directly. Test them through the public behavior.

## 2. Pick inputs that find bugs

For every input, test the partitions and their edges:
- **Numbers:** 0, 1, -1, the min and max allowed, one past each, very large, floats where ints are expected
- **Strings:** empty, whitespace, very long, unicode, different case, leading/trailing spaces
- **Collections:** empty, one item, many, duplicates, unsorted
- **Money:** amounts that round differently (x.xx5), totals checked to the cent
- **Dates:** month ends, Feb 29, Dec 31 to Jan 1, time zones, DST changes
- **Errors:** every documented error. Assert the exception type AND the message or field

Use parametrized tests for these tables (`@pytest.mark.parametrize`, `test.each`).
For logic with clear invariants (round-trips, sorting, totals), add **property-based tests**
(Hypothesis, fast-check). They find inputs you'd never think of.

## 3. Exact expectations

- Assert the exact value, not "truthy" or "not None".
- Write expected values by hand from the requirement. Never compute them with the same code
  you're testing.
- One behavior per test. The name says the behavior: `test_discount_applies_once`.

## 4. Keep them fast and isolated

- **Unit:** no network, no real database, no sleeping, no real clock. Inject or freeze time.
  Mock only true boundaries (HTTP clients, clocks, randomness), never the logic under test.
- **Integration:** use the real thing in a throwaway form, like a temporary directory, an
  in-memory or containerized database, or a local test server. Each test creates its own
  data and leaves nothing behind.
- Tests must pass in any order and in parallel.

## 5. Finish properly

- [ ] Every promise from step 1 has a test, including the error cases.
- [ ] Break the code on purpose (flip a `<`, drop a check) and confirm a test fails.
      Mutation tools automate this: `mutmut` (Python), `Stryker` (JS/TS).
- [ ] The whole suite runs in seconds. Slow tests get moved to integration.
- [ ] Coverage is checked for what's MISSING, not chased as a number.
