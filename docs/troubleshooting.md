# Troubleshooting

## Missing `OPENROUTER_API_KEY`

Symptom:

```text
missing required env vars: OPENROUTER_API_KEY
```

Fix:

```bash
export OPENROUTER_API_KEY=...
mpf doctor --provider openrouter --live
```

## No smoke cases found

Symptom:

```text
no smoke cases found at evals/smoke.jsonl
```

Fix:

```bash
mpf init-project
mpf run
```

## Provider returns 429 or unavailable

Use a focused live check:

```bash
mpf doctor --provider openrouter --live
```

If the provider is rate-limited, wait for quota reset, reduce fanout, or switch to the no-key
workflow for local CLI validation:

```bash
mpf init --preset minimal --overwrite
mpf doctor --live
mpf demo
```

## Model not found

Provider model slugs can change. Inspect the configured routes:

```bash
mpf models
mpf providers guide openrouter
```

Then update `~/.config/model-preflight/config.yaml` or regenerate a preset:

```bash
mpf init --provider openrouter --overwrite
```
