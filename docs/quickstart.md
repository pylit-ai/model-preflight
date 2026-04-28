# Quickstart

## One-provider path

```bash
uv tool install model-preflight
mpf init --provider nvidia
export NVIDIA_NIM_API_KEY=...
mpf doctor --live
mpf demo
```

Expected signal:

- `mpf doctor --live` prints a deployments table and `live check ok: group=...`.
- `mpf demo` prints JSON with `"passed": true` and `"failures": []`.

Then add project-local smoke cases:

```bash
cd my-project
mpf init-project
mpf run
```

Expected signal:

- `mpf init-project` writes `evals/smoke.jsonl`, `.model-preflight/README.md`, and a `.gitignore` entry.
- `mpf run` prints starter case JSON where each passing case has `"passed": true`.

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
It does not verify provider auth, quota, latency, or model quality.

## Provider setup

```bash
mpf providers list
mpf providers guide nvidia
mpf providers guide openrouter
mpf providers test nvidia
mpf providers test openrouter
```

NVIDIA Build / NIM is the primary high-capability open/open-weight endpoint option. OpenRouter is
still the lowest-friction discovery option because one API key can route to many model providers
through an OpenAI-compatible API.

```bash
mpf init --provider nvidia
export NVIDIA_NIM_API_KEY=...
mpf doctor --provider nvidia --live
```

| Provider | Best for | Env var | Setup |
|----------|----------|---------|-------|
| NVIDIA Build / NIM | Primary high-capability open/open-weight endpoint pool | `NVIDIA_NIM_API_KEY` | <https://build.nvidia.com/settings/api-keys> |
| OpenRouter | One-key first run with broad model access | `OPENROUTER_API_KEY` | <https://openrouter.ai/docs/api-reference/authentication> |
| Groq | Fast repeated calls after first-run setup works | `GROQ_API_KEY` | <https://console.groq.com/keys> |
| Cerebras | Fast inference experiments when current dev-tier limits fit | `CEREBRAS_API_KEY` | <https://inference-docs.cerebras.ai/> |
| Mistral | First-party Mistral model-family smoke checks | `MISTRAL_API_KEY` | <https://docs.mistral.ai/getting-started/quickstart/#account-setup> |

Secondary/overflow pool to add manually once the primary pool works: Google Gemini/Gemma,
Cloudflare Workers AI, GitHub Models, Hugging Face Inference Providers, and SambaNova.

Provider preset data is starter data, not a provider catalog guarantee. Check the provider's current
model catalog, pricing, and rate limits before depending on a route.
