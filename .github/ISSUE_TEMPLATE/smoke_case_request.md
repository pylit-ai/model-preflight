---
name: Smoke case request
about: Suggest a reusable JSONL smoke case for prototypes or CI.
title: "[Smoke case]: "
labels: smoke-case
assignees: ""
---

## Workflow

What kind of prototype or agent would this smoke case protect?

## Proposed case

```json
{"id":"example","prompt":"Return only: ok","expected_substrings":["ok"]}
```

## Failure mode caught

What provider, formatting, routing, or output-shape drift would this catch?

## Should this be default?

Explain whether this belongs in the starter `evals/smoke.jsonl`, docs, or examples only.
