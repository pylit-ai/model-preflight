# Quickstart

## One-provider path

```bash
uv tool install model-preflight
mpf init --provider openrouter
export OPENROUTER_API_KEY=...
mpf doctor --live
mpf demo
```

Then add project-local smoke cases:

```bash
cd my-project
mpf init-project
mpf run
```

## No-key path

```bash
mpf init --preset minimal
mpf doctor --live
mpf demo
mpf init-project
mpf run
```

The minimal preset uses an offline echo deployment. It verifies CLI wiring, config loading,
project file creation, JSONL parsing, scoring, and audit writing without contacting a provider.

## Provider setup

```bash
mpf providers list
mpf providers guide openrouter
```

Provider preset data is starter data, not a provider catalog guarantee. Check the provider's current
model catalog, pricing, and rate limits before depending on a route.
