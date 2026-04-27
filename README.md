# ModelPreflight

**Preflight checks for LLM prototypes.**

A tiny local gateway for LLM smoke tests, provider failover, and cheap prototype checks.

## Install

```bash
uvx model-preflight --help
uv add --dev model-preflight
# or
pip install model-preflight
```

## Install locally

```bash
uv pip install -e .
# or from another repo
uv add --dev --editable /absolute/path/to/model-preflight
```

## Configure once per machine

```bash
mpf init
$EDITOR ~/.config/model-preflight/config.yaml
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export CEREBRAS_API_KEY=...
export MISTRAL_API_KEY=...
mpf doctor
```

Both `mpf` and `model-preflight` are installed as console scripts.

## Use in projects

```bash
mpf models
mpf run examples/smoke_cases.jsonl
mpf pro "Return a robust answer to this toy task" --n 8
```

Python:

```python
from model_preflight import ModelGateway, load_config, pro_mode

gateway = ModelGateway(load_config())
print(gateway.text("Return only: ok", group="free_reasoning"))
print(pro_mode(gateway, "Solve this toy puzzle", n=8)["final"])
```

## Design

- Global provider/auth/routing lives in `~/.config/model-preflight/config.yaml`.
- Project-local checks only define cases, scoring, fixtures, and artifacts.
- LiteLLM handles provider-specific API quirks while ModelPreflight adds stable aliases and audit logs.
- The package can be used as a library, CLI, AutoHarness provider adapter, or FastAPI backend.

## Commands

```bash
mpf init
mpf doctor
mpf models
mpf run evals/smoke.jsonl
mpf pro "solve this toy task" --n 8
```

## Repo adapters

- `examples/autoharness_provider.py`: drop-in provider wrapper for AutoHarness.
- `examples/gpt_pro_mode_refactor.py`: refactors single-provider Pro Mode into shared routing.
- `examples/node_hook_example.mjs`: CLI bridge for JS/agent-hook projects.
- `skills/model-preflight/SKILL.md`: optional coding-agent skill for consistent usage.

## Non-goals

ModelPreflight is not a model leaderboard, a formal benchmark harness, a hosted gateway, or an authority on which endpoints are free today. It is a small preflight layer for early prototype checks.
