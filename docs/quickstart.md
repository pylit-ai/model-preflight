# Quickstart

## One-provider path

```bash
uv tool install model-preflight
export OPENROUTER_API_KEY=...
# or export NVIDIA_NIM_API_KEY=...
mpf init --provider openrouter
mpf ask "In one sentence, explain why checking an LLM route before wiring it into an app saves time."
```

Expected signal:

- `mpf init --provider openrouter` writes a machine-local config for the selected provider.
- `mpf ask` prints only the model response to stdout. Route/progress metadata goes to stderr.
- If a key, provider, or route is missing, the command prints the missing env var or route name.

Use doctor when you want a fuller diagnostics table:

```bash
mpf doctor --live
```

Expected signal: `live check ok: group=...`.

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
mpf demo
mpf init-project
mpf run
```

The minimal preset uses an offline echo deployment. It verifies CLI wiring, config loading,
project file creation, JSONL parsing, scoring, and audit writing without contacting a provider.
It does not verify provider auth, quota, latency, or model quality.

## One-off prompts and Pro Mode

Use `ask` for a single routed model call:

```bash
mpf ask "Write a short poem about how ModelPreflight makes free endpoint checks easy."
```

Use `pro` when the prompt is worth sampling multiple times and synthesizing through a judge group:

```bash
mpf pro "Compare three schema strategies for this extraction task" \
  -n 4 \
  --artifact .model-preflight/artifacts/pro-run.json
```

`-n 4` samples four candidate answers before the judge pass. Start low when testing paid routes;
fanout multiplies provider calls.

`mpf pro` prints the final answer to stdout by default. Diagnostics go to stderr, and the artifact
contains the prompt, provider/model routes, candidate responses, candidate errors, group winners,
and final judge output. Use `--json` only when you want the full candidate payload on stdout.

This is related to the self-consistency idea in LLM research: sample multiple reasoning paths, then
select or synthesize a better answer than a single greedy response. See Google's ICLR 2023 paper,
[Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://research.google/pubs/self-consistency-improves-chain-of-thought-reasoning-in-language-models/).

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

With no arguments, `mpf init` auto-detects visible keys in this order: OpenRouter, NVIDIA, Groq,
Cerebras, Mistral. Explicit `--provider` and `--preset` override auto-detection.

```bash
mpf init --provider nvidia
export NVIDIA_NIM_API_KEY=...
mpf doctor --provider nvidia --live
```

For local cross-project use, keep secrets in a private dotenv file and link it once:

```bash
mpf setup --env-file /path/to/private/.env
```

Agent and CI processes must receive the provider key in their own environment or through a linked
machine-local secret source. Use JSON output as the readiness gate:

```bash
mpf doctor --group free_reasoning --json
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

For custom config paths, JSON diagnostics, linked dotenv files, and YAML examples, see
[`configuration.md`](./configuration.md). For coding-agent setup prompts, see
[`agent-operations.md`](./agent-operations.md).
