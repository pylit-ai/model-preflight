---
name: model-preflight
description: Use this skill when a project needs quick LLM endpoint smoke tests, provider failover, or pro-mode fanout synthesis through the shared ModelPreflight package.
---

# ModelPreflight

## Rules

- Prefer `mpf ask` for the first human-facing value check, then `mpf doctor --live` for deeper
  diagnostics.
- Use deterministic fixture tests before paid or quota-limited provider tests.
- Treat rotating providers as development scaffolding, not publishable benchmark evidence.
- Pin provider, model id, date, prompt, params, and artifact path for any result used in a report.
- Keep project-specific smoke cases in the project; keep provider/auth/routing in ModelPreflight.
- Use `mpf init --preset minimal` when credentials are absent; it verifies local wiring, not model
  quality or provider auth.

## Common commands

```bash
mpf init --provider openrouter
mpf ask "Explain why preflighting this LLM route saves time."
mpf doctor --live
mpf models
mpf run
mpf pro "Compare three schema strategies" --n 4 --artifact .model-preflight/artifacts/pro-run.json
```

## Integration pattern

1. Add `model-preflight` as a dev dependency.
2. Store global provider config at `~/.config/model-preflight/config.yaml`.
3. Add a tiny project-local smoke manifest only for cases, scoring, and artifact paths.
4. Never duplicate provider keys or provider catalog config inside each repo.

## Agent specs

- `docs/agent-specs/setup-model-preflight.md`: use when adding ModelPreflight to a target repo.
- `docs/agent-specs/provider-drift-check.md`: use when diagnosing route/model/key drift.
