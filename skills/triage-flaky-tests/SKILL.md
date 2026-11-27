---
name: triage-flaky-tests
description: Decide whether failing tests are flaky, regressed, or genuinely broken by analysing results across many CI runs. Use when a test "fails sometimes", someone wants to add retries, or CI history needs triage.
---

# Triaging flaky tests

The most expensive mistake in test triage is calling a real regression "flaky" and
retrying it until it passes. Classify first, then act.

## 1. Get history, not one run

One run tells you nothing about flakiness. Collect JUnit XML from at least 5 runs (more
is better), oldest to newest. Then use the `flaky-hunter` tool if it's available:

```bash
pip install git+https://github.com/Kurtis-H/flaky-hunter
flaky-hunter path/to/junit-reports/ --format text
```

If the tool isn't available, build the pass/fail history per test by hand and apply the rules below.

## 2. Classify each failing test by its history

Look at the sequence of results, oldest to newest (✅ pass, ❌ fail, skips ignored):

| Pattern | Status | What it means |
|---|---|---|
| ✅❌✅✅❌✅❌ (alternating) | **flaky** | timing, ordering, shared state, environment |
| ✅✅✅✅❌❌❌ (passed, then failed every run since) | **regressed** | a real bug introduced at the first ❌. NOT flaky |
| ❌❌❌❌❌❌❌ | **broken** | consistently failing. Not flaky |
| ❌❌❌✅✅✅✅ | **recovered** | fixed. Nothing to do |

The key number is **flip rate**: how often the result changes between consecutive runs.
High flip rate means flaky. Failures with a flip rate near zero mean something broke and stayed broken.
Fail rate alone can't tell these apart: both examples above can have the same fail rate.

## 3. Act on the classification

- **Regressed:** find the change made between the last ✅ and the first ❌. Treat it as a
  product bug until proven otherwise. Never add retries.
- **Broken:** a real failure. Fix the test or the code; don't retry.
- **Flaky:** group failures by error signature (normalize timings and IDs: "Timeout 5012ms"
  and "Timeout 5098ms" are the same problem), then look for the cause:
  - waiting on fixed sleeps instead of a condition
  - tests sharing data or depending on run order
  - responses arriving out of order (race conditions)
  - time zones, dates, random data without a seed
  - external services
- **Quarantine** only flaky tests with 5+ runs AND a flip rate of 30% or more, and only with
  a ticket and an owner. Quarantine is a to-do list, not a fix.

## 4. Report

For each failing test give: status, history (the ✅/❌ string), flip rate, most common
error, and the recommended action. List regressions FIRST: they are the urgent ones.
