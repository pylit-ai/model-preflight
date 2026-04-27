---
name: model-preflight
description: Use this skill when a project needs quick LLM endpoint smoke tests, provider failover, or pro-mode fanout synthesis through the shared ModelPreflight package.
---

# ModelPreflight

## Rules

- Prefer `mpf doctor` before any live provider call.
- Use deterministic fixture tests before paid or quota-limited provider tests.
- Treat rotating providers as development scaffolding, not publishable benchmark evidence.
- Pin provider, model id, date, prompt, params, and artifact path for any result used in a report.
- Keep project-specific smoke cases in the project; keep provider/auth/routing in ModelPreflight.

## Common commands

```bash
mpf init
mpf doctor
mpf models
mpf run examples/smoke_cases.jsonl
mpf pro "Solve this toy task" --n 8 --sample-group free_fast --judge-group free_reasoning
```

## Integration pattern

1. Add `model-preflight` as a dev dependency.
2. Store global provider config at `~/.config/model-preflight/config.yaml`.
3. Add a tiny project-local smoke manifest only for cases, scoring, and artifact paths.
4. Never duplicate provider keys or provider catalog config inside each repo.
