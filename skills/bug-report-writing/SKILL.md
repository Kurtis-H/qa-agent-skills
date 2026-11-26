---
name: bug-report-writing
description: Turn a vague bug description into a complete, accurate bug report without inventing details or leaking sensitive data. Use when writing, rewriting or filing a bug report or issue.
---

# Writing bug reports a developer can act on

A good report lets someone reproduce the bug without asking a single question. A bad one
wastes a day. The worst one sends them to reproduce something that never happened.

## 1. Redact first

Before anything else, replace emails, API keys, tokens, passwords and card numbers with
placeholders like `[email]`. Never copy them into the report, even if the user wrote them.

## 2. Required sections

```
# <Specific title: what breaks, where. Not "X is broken".>

<One or two sentence summary>

## Steps to reproduce
1. <one action per step, at least two steps>

## Expected
## Actual          (include error messages word for word)
## Environment     (device, OS, browser/app version)
**Frequency:** every time / sometimes / once · **Suggested severity:** <level> (<why>)
## Evidence        (screenshots, logs, error IDs)
```

## 3. If something is missing, ask. Don't fill it in

Ask one short question per missing section, and only for the sections that are missing.
If the user doesn't know, write "unknown". Never guess.

## 4. The grounding rule (most important)

Every specific detail in the report must come from what the user said. Specific means:
numbers, versions, error codes, URLs, quoted messages, browser, device and OS names.

- User said "on my phone": write "on their phone", NOT "iPhone 15" or "Android 14".
- User said "it errors": ask for the message, don't write "500 Internal Server Error".
- Re-read your report before finishing. For each specific detail, find where the user said it.
  If you can't, remove it or mark it "(unconfirmed)".

## 5. Severity with a stated reason

- critical: data loss, security, money taken wrongly, nobody can log in, outage
- high: crash, blocked from a core task (can't check out, can't save), 5xx errors
- medium: wrong result, broken feature with a workaround
- low: cosmetic, typo, alignment
- Lower one level if it happened only once; never lower it if it happens every time.
- Always state the phrase that set the level: "high ('can't check out')".

## 6. Check for duplicates

If you can see existing issues, search for the same feature and symptom before filing.
Link likely duplicates instead of creating a new one.
