# First-Run UX Contract

## Objective

A new user should reach one successful ModelPreflight check before they need to understand provider
groups, edit YAML, or configure multiple provider accounts.

Activation target:

```bash
mpf init --provider openrouter
export OPENROUTER_API_KEY=...
mpf doctor --live
mpf demo
mpf ask "Return one sentence confirming the route works."
mpf init-project
mpf run
```

No-key validation target:

```bash
mpf init --preset minimal
mpf doctor --live
mpf demo
mpf init-project
mpf run
```

## MUST requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| UX-001 | First remote setup requires one provider and one env var. | `mpf init --provider nvidia` and `mpf init --provider openrouter` each write one enabled required deployment. |
| UX-002 | A no-key path validates CLI/project wiring. | `mpf init --preset minimal && mpf doctor --live && mpf demo && mpf init-project && mpf run`. |
| UX-003 | `doctor` only fails required selected deployments. | Tests cover required vs optional env vars and provider filters. |
| UX-004 | Live provider calls are opt-in. | Tests cover no-live doctor behavior through the offline flow; docs say live checks are opt-in. |
| UX-005 | Installed users do not need source-checkout examples. | `mpf demo`, `mpf init-project`, and default `mpf run` do not reference `examples/smoke_cases.jsonl`. |
| UX-006 | Smoke calls carry case metadata into audit rows. | Tests assert `runner=smoke` and `case_id`. |
| UX-007 | Pro Mode reports partial fanout failure instead of aborting if candidates succeed. | Tests simulate mixed success/failure. |
| UX-008 | `mpf ask` provides a clean one-off prompt path. | Tests cover stdout-only model text, stderr route/progress, `--quiet`, and JSON route metadata. |
| UX-009 | Pro Mode is human-readable by default and inspectable on demand. | Tests cover `-n`, final-only stdout, stderr diagnostics, `--json`, and `--artifact`. |
| UX-010 | Simple imports and help remain lightweight. | Tests assert top-level import does not import `litellm`. |

## SHOULD requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| UX-011 | Provider setup is discoverable from CLI. | `mpf providers list` and `mpf providers guide openrouter`. |
| UX-012 | Troubleshooting maps failures to commands. | `docs/troubleshooting.md`. |
| UX-013 | Package artifacts include preset files. | Wheel inspection checks `model_preflight/presets/*.yaml`. |

## Command behavior

`mpf init --provider nvidia` writes the NVIDIA Build / NIM preset and prints the env var to set.

`mpf init --provider openrouter` writes the OpenRouter preset and prints the env var to set.

`mpf init --preset minimal` writes an offline echo preset. It is for CLI and project workflow
validation, not model-quality evaluation.

`mpf doctor` validates config and required env vars for the default group unless `--group` or
`--provider` narrows the check. Optional/disabled providers do not block first run.

`mpf doctor --live` sends `Return only: ok` to the selected group and records audit metadata with
`phase=doctor_live`.

`mpf demo` runs a packaged smoke case. It uses the current config, so it is offline only when the
minimal preset is active.

`mpf ask` sends one prompt through the configured group. Model text goes to stdout. Route/progress
metadata goes to stderr unless `--quiet` is set. JSON output includes route metadata unless
`--hide-route` is set.

`mpf pro` fans out samples and synthesizes a final answer. By default, stdout contains only the final
answer. Diagnostics go to stderr. `--artifact` writes full prompt/routes/candidates/winners/final
diagnostics to disk, and `--json` prints the full candidate payload to stdout.

`mpf init-project` creates `evals/smoke.jsonl`, `.model-preflight/README.md`, and a `.gitignore`
entry for `.model-preflight/artifacts/`.

`mpf run` defaults to `evals/smoke.jsonl`. If the file is absent, it exits with code 2 and tells the
user to run `mpf init-project`.

`mpf providers add` is intentionally deferred. For now, use `mpf init --provider <provider>` to
regenerate provider-scoped config or edit YAML explicitly for advanced multi-provider setups.
