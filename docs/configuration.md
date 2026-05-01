# Configuration

ModelPreflight keeps provider routing machine-local and smoke cases project-local.

## Paths

ModelPreflight reads provider routes and secret-source references from your OS-specific user config
directory by default. Use `mpf paths` to print the exact path.

```bash
mpf paths
mpf init
mpf doctor
mpf models
```

Override the config path with either `--config` or `MODEL_PREFLIGHT_CONFIG`:

```bash
mpf init --config ./model-preflight.yaml
mpf doctor --config ./model-preflight.yaml --live

export MODEL_PREFLIGHT_CONFIG="$PWD/model-preflight.yaml"
mpf models
```

## Provider selection

With no `--provider` or `--preset`, `mpf init` checks visible environment variables in this order:

1. `OPENROUTER_API_KEY`
2. `NVIDIA_NIM_API_KEY`
3. `GROQ_API_KEY`
4. `CEREBRAS_API_KEY`
5. `MISTRAL_API_KEY`

OpenRouter is only the fallback starter when none of those keys are visible. Explicit `--provider`
and `--preset` always override auto-detection.

Provider setup is discoverable from the CLI:

```bash
mpf providers list
mpf providers guide nvidia
mpf providers guide openrouter
mpf providers test nvidia
mpf providers test openrouter
```

| Provider | Best for | Env var | Setup |
|----------|----------|---------|-------|
| NVIDIA Build / NIM | Primary high-capability open/open-weight endpoint pool | `NVIDIA_NIM_API_KEY` | [API keys](https://build.nvidia.com/settings/api-keys) |
| OpenRouter | One-key first run with broad model access | `OPENROUTER_API_KEY` | [Authentication docs](https://openrouter.ai/docs/api-reference/authentication) |
| Groq | Fast repeated calls after first-run setup works | `GROQ_API_KEY` | [Groq console](https://console.groq.com/keys) |
| Cerebras | Fast inference experiments when current dev-tier limits fit | `CEREBRAS_API_KEY` | [Cerebras inference docs](https://inference-docs.cerebras.ai/) |
| Mistral | First-party Mistral model-family smoke checks | `MISTRAL_API_KEY` | [Mistral API keys](https://docs.mistral.ai/getting-started/quickstart/#account-setup) |

Secondary/overflow pools to add manually once the primary pool works: Google Gemini/Gemma,
Cloudflare Workers AI, GitHub Models, Hugging Face Inference Providers, and SambaNova. See
[`PROVIDER_PRESETS.md`](./PROVIDER_PRESETS.md) for current preset notes and drift warnings.

## Secrets

Provider keys are not stored in ModelPreflight config. Use environment variables or link a
machine-local dotenv file that stays outside the package repo:

```bash
mpf setup --env-file /path/to/private/.env
```

Process env vars win over linked dotenv values. That keeps CI, production, and agent processes
compatible with standard secret injection.

If you use 1Password, see [`docs/secrets/1password.md`](./secrets/1password.md) for linked dotenv
and `op run` examples.

## Agent and CI diagnostics

Agent and CI processes need provider keys visible in their own environment or through a linked
machine-local secret source. Use JSON diagnostics for machine-readable readiness checks:

```bash
mpf doctor --group free_reasoning --json
```

`status: "ok"` means config and required keys are present. `error_code` distinguishes
`MISSING_REQUIRED_ENV`, `GROUP_NOT_FOUND`, and disabled matching provider/group cases.

## Config shape

The default config creates logical groups, then maps each group to one or more LiteLLM deployments:

```yaml
router:
  num_retries: 1
  timeout_seconds: 60
  default_group: free_reasoning
  audit_jsonl: null
artifacts_dir: ~/.cache/model-preflight/artifacts

deployments:
  - name: nvidia_nim_nemotron_3_super
    provider: nvidia
    group: free_reasoning
    model: nvidia_nim/nvidia/nemotron-3-super-120b-a12b
    api_key_env: NVIDIA_NIM_API_KEY
    enabled: true
    required: true
    status: best_effort
    setup_url: https://build.nvidia.com/settings/api-keys
    rpm: 10
    tier: reasoning
```

Provider presets are starter data, not authoritative claims about free availability:

- user-local config wins over bundled defaults
- `mpf doctor` fails fast when required keys are missing
- optional/disabled providers do not block first-run checks
- live checks should be opt-in in CI
- endpoint names, quotas, pricing, and behavior can change without this repo knowing
