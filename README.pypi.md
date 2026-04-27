# ModelPreflight

**Preflight checks for LLM prototypes.**

A tiny local gateway for LLM smoke tests, provider failover, and cheap prototype checks before you wire an LLM into something bigger.

[![CI](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml/badge.svg)](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/model-preflight?label=PyPI)](https://pypi.org/project/model-preflight/)
![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey.svg)
![LiteLLM](https://img.shields.io/badge/router-LiteLLM-informational)

| If you want to... | Start here |
|-------------------|------------|
| Get one green check quickly | [60-second start](#60-second-start) |
| Try it without keys | [No-key demo path](#no-key-demo-path) |
| Configure provider groups once | [Machine-local config](#machine-local-config) |
| Run project smoke cases | [Smoke tests](#smoke-tests) |
| Fan out a one-off prompt | [Pro Mode](#pro-mode) |
| Use it as a Python helper | [Library usage](#library-usage) |

ModelPreflight keeps provider setup **machine-local** and keeps smoke cases **project-local**. It gives prototypes stable model-group aliases, simple failover, and JSONL audit logs without becoming a benchmark harness or hosted gateway.

## 60-second start

```bash
uvx model-preflight --help

# In a persistent tool or project environment:
uv tool install model-preflight
# or:
pipx install model-preflight
```

Pick one provider, set one key, and run one live check:

```bash
mpf init --provider openrouter
export OPENROUTER_API_KEY=...
mpf doctor --live
mpf demo
```

Add checks to a project:

```bash
cd my-project
mpf init-project
mpf run
```

Both `mpf` and `model-preflight` are installed as console scripts.

ModelPreflight catches missing keys, broken provider routes, prompt formatting regressions, output-shape drift, accidental model/provider changes, and "this worked yesterday" prototype failures before you wire the LLM call into something larger.

## No-key demo path

Use the minimal offline preset when you want to test the CLI and project workflow without a provider account:

```bash
mpf init --preset minimal
mpf doctor --live
mpf demo
mpf init-project
mpf run
```

## Machine-local config

ModelPreflight reads provider routes from `~/.config/model-preflight/config.yaml` by default. Override the path with either `--config` or `MODEL_PREFLIGHT_CONFIG`.

```bash
mpf init --provider openrouter
mpf doctor
mpf models
```

The default config creates logical groups, then maps each group to one or more LiteLLM deployments:

```yaml
router:
  num_retries: 1
  timeout_seconds: 60
  default_group: free_reasoning
  audit_jsonl: null
artifacts_dir: ~/.cache/model-preflight/artifacts

deployments:
  - name: openrouter_gpt_oss_120b_free
    provider: openrouter
    group: free_reasoning
    model: openrouter/openai/gpt-oss-120b:free
    api_key_env: OPENROUTER_API_KEY
    enabled: true
    required: true
    status: best_effort
    setup_url: https://openrouter.ai/docs/api-reference/authentication
    rpm: 18
    tier: reasoning
```

Provider presets are best-effort starter data, not authoritative claims about free availability. User-local config wins over bundled defaults, optional/disabled providers do not block first-run checks, and endpoint names, quotas, pricing, and behavior can change without this package knowing.

## Smoke tests

Smoke cases are JSONL files owned by the project that is doing the prototype work.

```jsonl
{"id":"basic-ok","prompt":"Return only: ok","expected_substrings":["ok"]}
{"id":"avoid-word","prompt":"Answer yes without using the word nope","forbidden_substrings":["nope"]}
```

Run them with:

```bash
mpf run
# or:
mpf run path/to/smoke_cases.jsonl
```

`mpf run` prints JSON results and exits non-zero if any case fails.

## Pro Mode

`mpf pro` fans out a one-off prompt, then synthesizes a final answer through a judge group.

```bash
mpf pro "Suggest three robust JSON schemas for this toy extraction task" --n 8
```

Defaults:

| Option | Default | Role |
|--------|---------|------|
| `--n` | `8` | number of sampled answers |
| `--sample-group` | `free_fast` | fanout group |
| `--judge-group` | `free_reasoning` | synthesis group |

Fanout multiplies live provider calls. Keep `--n` low while testing, use restricted provider keys where available, and review provider dashboards when running against paid endpoints.

## Library usage

```python
from model_preflight import ModelGateway, load_config, pro_mode

gateway = ModelGateway(load_config())

print(gateway.text("Return only: ok", group="free_reasoning"))

result = pro_mode(gateway, "Solve this toy puzzle", n=8)
print(result["final"])
```

The library API is intentionally thin:

- `load_config()` reads the same machine-local config as the CLI
- `ModelGateway` wraps LiteLLM Router with stable group aliases and audit logging
- `pro_mode()` runs fanout plus synthesis for one-off prototype prompts

## Audit artifacts

By default, ModelPreflight writes audit logs under:

```text
~/.cache/model-preflight/artifacts/audit.jsonl
```

Each live call should be traceable enough to debug provider drift: timestamp, logical group, resolved provider/model when available, prompt or case metadata, latency, token usage when available, and response id when available.

## Non-goals

ModelPreflight is not a model leaderboard, a formal benchmark framework, a hosted inference gateway, a provider catalog authority, or proof that an endpoint is free, fast, or available today.
