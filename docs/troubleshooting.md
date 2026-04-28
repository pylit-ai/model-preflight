# Troubleshooting

## `mpf init` chose an unexpected provider

With no `--provider` or `--preset`, `mpf init` chooses the first visible supported key in this
order: OpenRouter, NVIDIA, Groq, Cerebras, Mistral. If no supported key is visible, it writes the
OpenRouter starter config and tells you to export `OPENROUTER_API_KEY`.

Fix:

```bash
mpf init --provider nvidia --overwrite
# or use the provider whose key should drive this machine-local config
mpf doctor --json
```

For agents and CI, the key must be visible in that process environment. A key set in another shell,
desktop session, or secret store does not count until it is injected into the process running
`mpf`.

For local cross-project use, link the private dotenv file once:

```bash
mpf setup --env-file /path/to/private/.env
```

## Missing `NVIDIA_NIM_API_KEY`

Symptom:

```text
missing required env vars: NVIDIA_NIM_API_KEY
```

Fix:

```bash
export NVIDIA_NIM_API_KEY=...
mpf doctor --provider nvidia --live
```

If the live check fails with a model-not-found style error, open the NVIDIA Build model page,
confirm the current API sample/model slug, and update `model:` in your local
config path shown by `mpf paths`.

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

## Agent reports missing keys

Use machine-readable diagnostics before running live provider tests:

```bash
mpf doctor --group free_reasoning --json
```

Read `error_code`:

- `MISSING_REQUIRED_ENV` means the selected group exists, but the required key is absent.
- `NO_READY_DEPLOYMENT` means the selected group exists, but none of its enabled deployments have
  usable credentials.
- `GROUP_NOT_FOUND` means the requested group is not configured.
- `GROUP_DISABLED` means a matching provider/group exists only in disabled deployments.

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

Then update the config path shown by `mpf paths` or regenerate a preset:

```bash
mpf init --provider openrouter --overwrite
```
