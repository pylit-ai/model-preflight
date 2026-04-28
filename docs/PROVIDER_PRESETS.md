# Provider Presets

Provider presets are best-effort starter data, not authoritative claims about free availability.
See [`MODEL_SELECTION.md`](./MODEL_SELECTION.md) for why each packaged default model was chosen.

Rules:

- Bundled presets are conservative defaults.
- User-local config always wins over bundled presets.
- `mpf init` auto-detects visible provider keys in deterministic order: OpenRouter, NVIDIA, Groq,
  Cerebras, Mistral.
- OpenRouter is the fallback starter only when no supported provider key is visible.
- `mpf init --provider nvidia` is the primary high-capability remote preset.
- `mpf init --provider openrouter` is the explicit OpenRouter remote preset.
- `mpf init --preset minimal` is the no-key offline preset for CLI/demo validation.
- `mpf doctor` should fail fast only when required keys for the selected group/provider are missing.
- `mpf doctor --json` is the stable readiness contract for agents and CI.
- Optional or disabled providers should be reported as skipped/warnings, not first-run failures.
- Live provider checks should be opt-in in CI.
- Any free/dev endpoint may disappear, rate-limit, or change model behavior.

A provider row should include enough provenance to debug drift:

```yaml
name: groq_gpt_oss_120b
provider: groq
group: free_fast
model: groq/openai/gpt-oss-120b
api_key_env: GROQ_API_KEY
enabled: false
required: false
rpm: 10
tier: fast
last_verified: "2026-04-27"
status: optional
```

Default model policy:

- NVIDIA and OpenRouter defaults should prefer the best currently documented free/dev capability
  route, not legacy GPT-OSS slugs.
- Groq and Cerebras can still default to GPT-OSS when it is the most stable production/high-throughput
  route on that provider.
- Preview models can appear as optional alternatives, but should not silently become defaults without
  deprecation and quota review.

Current packaged presets:

| Preset | Purpose | Required key |
|--------|---------|--------------|
| `minimal` | Offline/no-key CLI and project workflow validation | none |
| `nvidia` | Primary high-capability open/open-weight endpoint path | `NVIDIA_NIM_API_KEY` |
| `openrouter` | One-provider first run | `OPENROUTER_API_KEY` |
| `multi-free-dev` | Advanced multi-provider starter with optional fast providers disabled | `OPENROUTER_API_KEY` |

Provider commands:

```bash
mpf providers list
mpf providers guide nvidia
mpf providers guide openrouter
mpf providers test nvidia
mpf providers test openrouter
```

Agent process requirements:

- Provider keys must be visible in the agent or CI process environment, not only in an interactive
  parent shell.
- Use `mpf doctor --group free_reasoning --json` before live tests.
- Treat `MISSING_REQUIRED_ENV`, `GROUP_NOT_FOUND`, and disabled matching provider/group errors as
  distinct setup failures.

Provider setup links:

| Provider | Preset | Required env var | Setup |
|----------|--------|------------------|-------|
| NVIDIA Build / NIM | `nvidia` | `NVIDIA_NIM_API_KEY` | <https://build.nvidia.com/settings/api-keys> |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | <https://openrouter.ai/docs/api-reference/authentication> |
| Groq | `multi-free-dev` | optional `GROQ_API_KEY` | <https://console.groq.com/keys> |
| Cerebras | `multi-free-dev` | optional `CEREBRAS_API_KEY` | <https://inference-docs.cerebras.ai/> |
| Mistral | `multi-free-dev` | optional `MISTRAL_API_KEY` | <https://docs.mistral.ai/getting-started/quickstart/#account-setup> |

NVIDIA is the primary capability-oriented path. OpenRouter is the easiest discovery path: one key,
broad model access, OpenAI-compatible API. The other primary-pool providers are useful once
first-run routing works and you want faster or more provider-specific smoke checks.

Secondary/overflow providers are intentionally documented before being packaged as presets:

| Provider | Use | Setup |
|----------|-----|-------|
| Google Gemini / Gemma | Independent Gemma-family sanity checks | <https://ai.google.dev/gemini-api/docs/pricing> |
| Cloudflare Workers AI | Cheap edge/baseline checks | <https://developers.cloudflare.com/workers-ai/> |
| GitHub Models | GitHub-native prototyping | <https://docs.github.com/en/billing/concepts/product-billing/github-models> |
| Hugging Face Inference Providers | Breadth/discovery with tiny monthly credits | <https://huggingface.co/docs/inference-providers/pricing> |
| SambaNova Cloud | Trial-credit overflow for open models | <https://cloud.sambanova.ai/plans> |
