---
name: write-playwright-tests
description: Write Playwright end-to-end and API tests that catch real bugs instead of proving a page loaded. Use when asked to add, write or improve Playwright tests for a web app or API.
---

# Writing Playwright tests that catch bugs

A test is only worth writing if it would FAIL when the feature breaks. Before writing each
test, name the bug it catches. If you can't, don't write it.

## 1. Read the rules before the UI

Find the stated rules first (requirements, help text, validation messages, API docs).
Every rule becomes at least one test. Rules hide in phrases like "at least", "up to",
"once", "rounded", "case-insensitive", "only", "every".

## 2. For every rule, test the edges, not just the middle

| Kind of rule | Tests to write |
|---|---|
| A limit ("at least 8 characters", "max 50") | exactly at the limit, one below, one above |
| Money | compute the expected value BY HAND to the cent and assert the exact string |
| "Once" / "only one" | do the action twice; assert the second time changes nothing |
| Quantities | go below the minimum; assert it stops there |
| Lists, paging | walk every page; assert the count matches the total |
| Sorting | compare against the same values sorted in code; check numbers sort numerically |
| Search | different capitalization; no results; partial matches |
| Dates | end of month, leap years, Dec to Jan, and the same test in several time zones with `test.use({ timezoneId })` |
| Two things with the same name | act on one; assert the other is untouched |
| Errors | force the failure (bad input, a server error); assert a message appears AND loading stops |
| Async / typing | type, pause, type more; wait for the slow response; assert what's on screen still matches |

## 3. Assert outcomes, not activity

- Assert exact text and values: `toHaveText('$99.56')`, not `toBeVisible()`.
- Assert what should NOT happen too: the old error is gone, the other item still exists.
- Count network requests to catch double submits and request spam:
  ```ts
  const sent: string[] = [];
  page.on('request', r => { if (r.url().includes('/api/signup')) sent.push(r.method()); });
  await submit.dblclick();
  expect(sent).toHaveLength(1);
  ```
- Test the API directly with values the UI never sends (0, -1, "abc", 1.5, huge numbers) and
  assert the status code (usually 400), not just "it didn't crash".

## 4. Structure

- Locators by role and label first (`getByRole`, `getByLabel`), `data-testid` second, CSS last.
  A test that can't find a field by its label has found an accessibility bug.
- Arrange through the API (fast), assert through the UI (what users see).
- Unique test data per test (`Date.now()` + random suffix), so tests can run in parallel and
  re-run against a database that isn't reset.
- Never `waitForTimeout` to wait for the app. Wait for a response, a locator state or URL.
  The one exception: deliberately simulating a user pausing, with a comment saying so.
- No retries to make a test pass. A test that needs a retry has found a race condition.

## 5. Before you finish

- [ ] Every stated rule has a test at its boundary.
- [ ] Every test would fail if its feature broke (mentally delete the feature; does the test go red?).
- [ ] At least one negative test per form or endpoint.
- [ ] All tests pass against the current correct build. If one fails, investigate: it may be
      a real bug. Never weaken an assertion just to make it pass. Report it instead.
