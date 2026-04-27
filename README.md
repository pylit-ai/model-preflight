<div align="center">

# <img src="https://img.shields.io/badge/--16a34a?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxwYXRoIGQ9Ik0xMiAyMmg4IiAvPgogIDxwYXRoIGQ9Ik0xMiAxOHYtNCIgLz4KICA8cGF0aCBkPSJNMTIgMTRhNyA3IDAgMSAwLTcgNyIgLz4KICA8cGF0aCBkPSJNMTUgOWwtMyAzLTMtMyIgLz4KPC9zdmc%2BCg%3D%3D" height="48" align="center"> **ModelPreflight**

**Preflight checks for LLM prototypes.**

**A tiny local gateway for smoke tests, provider failover, and cheap prototype checks before you wire an LLM into something bigger.**

[![CI](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml/badge.svg)](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/model-preflight?label=PyPI)](https://pypi.org/project/model-preflight/)
![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey.svg)
![LiteLLM](https://img.shields.io/badge/router-LiteLLM-informational)

| If you want to... | Start here |
|-------------------|------------|
| Try it in a few commands | [Quick start](#quick-start) |
| Configure provider groups once | [Machine-local config](#machine-local-config) |
| Run project smoke cases | [Smoke tests](#smoke-tests) |
| Fan out a one-off prompt | [Pro Mode](#pro-mode) |
| Use it as a Python helper | [Library usage](#library-usage) |

---

ModelPreflight keeps provider setup **machine-local** and keeps smoke cases **project-local**. It gives prototypes stable model-group aliases, simple failover, and JSONL audit logs without becoming a benchmark harness or hosted gateway.

</div>

---

<details>
<summary><img src="https://img.shields.io/badge/--0ea5e9?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIiAvPgogIDxwYXRoIGQ9Ik0xMiAxNnYtNCIgLz4KICA8cGF0aCBkPSJNMTIgOGguMDEiIC8%2BCjwvc3ZnPgo%3D" height="24" align="center"> <b>Why this repo exists</b></summary>

Early LLM prototypes often need a quick answer to a practical question: "Can this prompt, model group, or provider route work well enough to keep building?"

ModelPreflight gives you a lightweight layer for that stage:

- one global config for provider credentials and routing
- project-local JSONL smoke cases
- stable aliases such as `free_reasoning` and `free_fast`
- best-effort failover through LiteLLM
- audit records for live calls

</details>

<details>
<summary><img src="https://img.shields.io/badge/--9ca3af?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIiAvPgogIDxwYXRoIGQ9Im05IDEyIDIgMiA0LTQiIC8%2BCjwvc3ZnPgo%3D" height="24" align="center"> <b>When to use it</b></summary>

Use ModelPreflight when:

- a prototype needs cheap LLM smoke checks before deeper eval work
- several projects should share the same local provider setup
- you want logical groups instead of hard-coding provider/model IDs everywhere
- provider quotas, model slugs, or dev-tier availability may drift
- you need enough provenance to debug "which model answered this?"

</details>

<details>
<summary><img src="https://img.shields.io/badge/--f97316?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxwYXRoIGQ9Im0yMS43MyAxOC04LTE0YTIgMiAwIDAgMC0zLjQ4IDBsLTggMTRBMiAyIDAgMCAwIDQgMjFoMTZhMiAyIDAgMCAwIDEuNzMtMyIgLz4KICA8cGF0aCBkPSJNMTIgOXY0IiAvPgogIDxwYXRoIGQ9Ik0xMiAxN2guMDEiIC8%2BCjwvc3ZnPgo%3D" height="24" align="center"> <b>What it is not</b></summary>

ModelPreflight is not:

- a model leaderboard
- a formal benchmark framework
- a hosted inference gateway
- a provider catalog authority
- proof that an endpoint is free, fast, or available today

Bundled provider presets are starter data. Check each provider's current catalog and terms before relying on a route.

</details>

## Quick start

```bash
uvx model-preflight --help

# In a persistent tool or project environment:
uv tool install model-preflight
# or:
pipx install model-preflight
```

Configure once per machine:

```bash
mpf init
$EDITOR ~/.config/model-preflight/config.yaml
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export CEREBRAS_API_KEY=...
export MISTRAL_API_KEY=...
mpf doctor
```

Run it in a project:

```bash
mpf models
mpf run examples/smoke_cases.jsonl
mpf pro "Return a robust answer to this toy task" --n 8
```

Both `mpf` and `model-preflight` are installed as console scripts.

<details open>
<summary><img src="https://img.shields.io/badge/--4f46e5?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxsaW5lIHgxPSI2IiB4Mj0iNiIgeTE9IjMiIHkyPSIxNSIgLz4KICA8Y2lyY2xlIGN4PSIxOCIgY3k9IjYiIHI9IjMiIC8%2BCiAgPGNpcmNsZSBjeD0iNiIgY3k9IjE4IiByPSIzIiAvPgogIDxwYXRoIGQ9Ik0xOCA5YTkgOSAwIDAgMS05IDkiIC8%2BCjwvc3ZnPgo%3D" height="24" align="center"> <b>Install options</b></summary>

**PyPI or isolated tool install**

```bash
uv tool install model-preflight
# or:
pipx install model-preflight
mpf --help
```

**Project dependency**

```bash
uv add --dev model-preflight
# or:
pip install model-preflight
```

**Editable checkout**

```bash
git clone https://github.com/pylit-ai/model-preflight.git
cd model-preflight
uv pip install -e .
# or from another repo:
uv add --dev --editable /absolute/path/to/model-preflight
```

ModelPreflight requires Python 3.11+.

</details>

---

## Machine-local config

ModelPreflight reads provider routes from `~/.config/model-preflight/config.yaml` by default. Override the path with either `--config` or `MODEL_PREFLIGHT_CONFIG`.

```bash
mpf init
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
  - name: groq_gpt_oss_120b
    group: free_fast
    model: groq/openai/gpt-oss-120b
    api_key_env: GROQ_API_KEY
    rpm: 10
    tier: fast
```

<details>
<summary><img src="https://img.shields.io/badge/--64748b?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxwYXRoIGQ9Ik05LjY3MSA0LjEzNmEyLjM0IDIuMzQgMCAwIDEgNC42NTkgMCAyLjM0IDIuMzQgMCAwIDAgMy4zMTkgMS45MTUgMi4zNCAyLjM0IDAgMCAxIDIuMzMgNC4wMzMgMi4zNCAyLjM0IDAgMCAwIDAgMy44MzEgMi4zNCAyLjM0IDAgMCAxLTIuMzMgNC4wMzMgMi4zNCAyLjM0IDAgMCAwLTMuMzE5IDEuOTE1IDIuMzQgMi4zNCAwIDAgMS00LjY1OSAwIDIuMzQgMi4zNCAwIDAgMC0zLjMyLTMuOTE1IDIuMzQgMi4zNCAwIDAgMS0yLjMzLTQuMDMzIDIuMzQgMi4zNCAwIDAgMCAwLTMuODMxQTIuMzQgMi4zNCAwIDAgMSA2LjM1IDYuMDUxYTIuMzQgMi4zNCAwIDAgMCAzLjMxOS0xLjkxNSIgLz4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIzIiAvPgo8L3N2Zz4K" height="24" align="center"> <b>Provider preset discipline</b></summary>

Provider presets are best-effort starter data, not authoritative claims about free availability.

- user-local config wins over bundled defaults
- `mpf doctor` fails fast when required keys are missing
- live checks should be opt-in in CI
- endpoint names, quotas, pricing, and behavior can change without this repo knowing

See [`docs/PROVIDER_PRESETS.md`](./docs/PROVIDER_PRESETS.md) for the preset rules.

</details>

<details>
<summary><img src="https://img.shields.io/badge/--06b6d4?style=flat&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9IndoaXRlIgogIHN0cm9rZS13aWR0aD0iMiIKICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIKPgogIDxyZWN0IHdpZHRoPSI3IiBoZWlnaHQ9IjciIHg9IjMiIHk9IjMiIHJ4PSIxIiAvPgogIDxyZWN0IHdpZHRoPSI3IiBoZWlnaHQ9IjciIHg9IjE0IiB5PSIzIiByeD0iMSIgLz4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI3IiB4PSIxNCIgeT0iMTQiIHJ4PSIxIiAvPgogIDxyZWN0IHdpZHRoPSI3IiBoZWlnaHQ9IjciIHg9IjMiIHk9IjE0IiByeD0iMSIgLz4KPC9zdmc%2BCg%3D%3D" height="24" align="center"> <b>Custom config path</b></summary>

```bash
mpf init --config ./model-preflight.yaml
mpf doctor --config ./model-preflight.yaml

export MODEL_PREFLIGHT_CONFIG="$PWD/model-preflight.yaml"
mpf models
```

Use environment variables for secrets. Do not commit provider keys.

</details>

---

## Smoke tests

Smoke cases are JSONL files owned by the project that is doing the prototype work.

```jsonl
{"id":"basic-ok","prompt":"Return only: ok","expected_substrings":["ok"]}
{"id":"avoid-word","prompt":"Answer yes without using the word nope","forbidden_substrings":["nope"]}
```

Run them with:

```bash
mpf run examples/smoke_cases.jsonl
```

`mpf run` prints JSON results and exits non-zero if any case fails.

<details>
<summary><strong>Case fields</strong></summary>

Each smoke case supports:

- `id`: stable case identifier
- `prompt`: user prompt sent to the configured model group
- `group`: optional model group override
- `expected_substrings`: strings that must appear in the answer
- `forbidden_substrings`: strings that must not appear in the answer

These checks are intentionally simple. They are meant to catch obvious routing, prompt, and regression problems before you spend time on heavier evals.

</details>

---

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

<details>
<summary><img src="https://img.shields.io/badge/--f59e0b?style=flat&logo=lightning&logoColor=white" height="24" align="center"> <b>Cost and quota note</b></summary>

Fanout multiplies live provider calls. Keep `--n` low while testing, use restricted provider keys where available, and review provider dashboards when running against paid endpoints.

ModelPreflight records audit rows for live calls, but it does not enforce provider billing limits beyond your configured routing and provider-side controls.

</details>

---

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

---

## Audit artifacts

By default, ModelPreflight writes audit logs under:

```text
~/.cache/model-preflight/artifacts/audit.jsonl
```

Each live call should be traceable enough to debug provider drift:

- timestamp
- logical group
- resolved provider/model when returned by the provider
- prompt or case metadata
- latency
- token usage when available
- response id when available

See [`docs/EVAL_PROVENANCE.md`](./docs/EVAL_PROVENANCE.md) for provenance expectations.

---

## Repo adapters

| Path | Purpose |
|------|---------|
| [`examples/autoharness_provider.py`](./examples/autoharness_provider.py) | Drop-in provider wrapper for AutoHarness-style experiments |
| [`examples/gpt_pro_mode_refactor.py`](./examples/gpt_pro_mode_refactor.py) | Example refactor from single-provider Pro Mode to shared routing |
| [`examples/node_hook_example.mjs`](./examples/node_hook_example.mjs) | CLI bridge for JS or agent-hook projects |
| [`skills/model-preflight/SKILL.md`](./skills/model-preflight/SKILL.md) | Optional coding-agent skill for consistent usage |

<details>
<summary><strong>Command reference</strong></summary>

```bash
mpf init
mpf doctor
mpf models
mpf run evals/smoke.jsonl
mpf pro "solve this toy task" --n 8
```

</details>

<details>
<summary><strong>Contributor workflow</strong></summary>

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

Package metadata lives in [`pyproject.toml`](./pyproject.toml). Tests live under [`tests/`](./tests/).

</details>

---

## Design principles

- Global provider/auth/routing lives in `~/.config/model-preflight/config.yaml`.
- Project-local checks define cases, scoring, fixtures, and artifacts.
- LiteLLM handles provider-specific API quirks.
- ModelPreflight adds stable aliases, lightweight failover, and audit logs.
- Deterministic tests should run before live provider checks.

For the product scope and non-goals, see [`docs/NORTHSTAR.md`](./docs/NORTHSTAR.md).

