---
name: load-testing
description: Design, write and interpret load tests with k6 - realistic scenarios, explicit pass/fail thresholds, and finding the bottleneck rather than just reporting slowness. Use when asked to load test, stress test, performance test or benchmark an API or website.
---

# Load testing with k6

A load test without pass/fail criteria is just a chart. Decide what "good" means first,
then design the traffic, then find out WHY it's slow when it is.

## 1. Agree the targets first

Write them down as thresholds before writing any script, for example:
- 95% of requests under 300 ms (`p(95)<300`) and 99% under 1 s
- error rate under 1% (`rate<0.01`)
- at the expected peak traffic, plus headroom (e.g. 2× peak)

If nobody knows the numbers, propose some and say they're assumptions.

## 2. Pick the right test type

| Type | Shape | Answers |
|---|---|---|
| **Smoke** | 1–2 users, 30 s | does the script work at all? (always run first) |
| **Load** | ramp to expected traffic, hold 5–15 min | do we meet targets on a normal busy day? |
| **Stress** | keep ramping past expected | where does it break, and how? |
| **Spike** | sudden jump, then drop | does it survive a burst, and recover? |
| **Soak** | expected traffic for hours | leaks, slow growth, connection exhaustion |

## 3. Write realistic scripts

```js
export const options = {
  scenarios: { browse: { executor: 'ramping-vus', stages: [
    { duration: '2m', target: 50 }, { duration: '10m', target: 50 }, { duration: '1m', target: 0 } ] } },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{name:search}': ['p(95)<300'],
    checks: ['rate>0.99'],
  },
};
```

- **Ramp up and down.** Never start at full load.
- **Think time** (`sleep(1 + Math.random() * 2)`) between actions, like real users.
- **Check responses** (`check(res, { 'status 200': r => r.status === 200 })`). A fast
  error page is not a fast response.
- **Tag requests** (`tags: { name: 'search' }`) so dynamic URLs group into one metric.
- **Realistic data:** different users, different search terms, not the same cached request.
- Log in once in `setup()`, not on every iteration, unless logging in is what you're testing.

## 4. Run it safely

- Only against systems you own or have written permission to test. Load tests look like attacks.
- Never against production without an agreed window.
- Run from a machine that isn't itself the bottleneck. Watch the load generator's CPU.

## 5. Find the bottleneck, don't just report the number

When thresholds fail, line up the k6 timeline with server metrics (CPU, memory, database
connections, slow query log, GC pauses, queue depth). Common culprits:
- one query per list item (N+1) or a missing index: database time grows with data
- no pagination limit: response size grows with data
- a memory leak: latency and memory climb steadily during a soak test
- lock contention: fine with a few users, collapses with many
- a cache that expires all at once: periodic spikes

Report: the target, the result, the evidence (graphs or numbers), the suspected cause, and the next step.
