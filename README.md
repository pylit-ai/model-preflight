<div align="center">

# <img src="https://raw.githubusercontent.com/pylit-ai/model-preflight/main/docs/assets/readme-icons/preflight.svg" height="48" align="center" alt="ModelPreflight compass icon"> **ModelPreflight**

**Find out which cheap or free-ish LLM endpoints can carry your prototype before you wire them into your app.**

ModelPreflight turns scattered provider keys into stable local groups like `free_reasoning`
and `free_fast`, then lets you smoke-test prompts, fan out one-off questions, and fail over
between providers without hard-coding model IDs everywhere.

[![CI](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml/badge.svg)](https://github.com/pylit-ai/model-preflight/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/model-preflight?label=PyPI)](https://pypi.org/project/model-preflight/)
![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey.svg)
![LiteLLM](https://img.shields.io/badge/router-LiteLLM-informational)

<img src="https://raw.githubusercontent.com/pylit-ai/model-preflight/main/docs/assets/hero.png" alt="ModelPreflight CLI preview showing provider preflight workflow" width="900">

<!-- TODO: Add terminal demo GIF showing no-key setup, mpf demo, and mpf run output. -->
<!-- TODO: Add product screenshot showing live provider diagnostics with JSON mode. -->
<!-- TODO: Add 60-second setup video link. -->

| If you want to... | Start here |
|-------------------|------------|
| Get one green check now | [First green check](#first-green-check) |
| See the free/dev endpoint menu | [Free endpoint map](#free-endpoint-map) |
| Try the payoff after setup | [Run one check, then ask the pool](#run-one-check-then-ask-the-pool) |
| Try it without keys | [No-key demo path](#no-key-demo-path) |
| Run project smoke cases | [Smoke tests](#smoke-tests) |
| Compare adjacent tools | [ModelPreflight vs LiteLLM vs promptfoo vs Langfuse](./docs/comparison.md) |
| Use it as a Python helper | [Library usage](#library-usage) |

---

ModelPreflight keeps provider setup **machine-local** and smoke cases **project-local**. It is
not a hosted gateway, model leaderboard, or pricing oracle. It is the fast local preflight layer
between "I found a promising free/dev endpoint" and "this provider is now wired into my product."

</div>

---

## First green check

Run the CLI without creating accounts or exporting provider keys:

```bash
uvx model-preflight --help
uvx model-preflight init --preset minimal
uvx model-preflight demo
```

Expected signal:

```json
[
  {
    "id": "demo-ok",
    "passed": true,
    "failures": [],
    "text": "ok"
  }
]
```

Next command if this fails:

```bash
uvx model-preflight doctor
```

Then install persistently when you want `mpf` as the short command:

```bash
uv tool install model-preflight
mpf init --preset minimal
mpf demo
```

---

## Free endpoint map

The high-value path is simple: collect provider keys once, let ModelPreflight group them, then
ask `free_reasoning` or `free_fast` instead of memorizing every provider's model slug and quota
page.

Provider notes last reviewed: 2026-04-30. Catalogs, free tiers, quotas, and model IDs can change
without a ModelPreflight release; use each provider console plus `mpf doctor --live` as the current
truth for your account.

| Provider | What it gives a prototype | Default group | Key env var | Setup |
|----------|---------------------------|---------------|-------------|-------|
| OpenRouter | Lowest-friction first run; one API key can route to free-tagged and paid models | `free_reasoning` | `OPENROUTER_API_KEY` | [Auth docs](https://openrouter.ai/docs/api-reference/authentication) |
| NVIDIA Build / NIM | High-capability open/open-weight hosted endpoints while the current dev access fits | `free_reasoning` | `NVIDIA_NIM_API_KEY` | [API keys](https://build.nvidia.com/settings/api-keys) |
| Groq | Very fast repeated calls for fanout and smoke checks when free-plan limits fit | `free_fast` | `GROQ_API_KEY` | [Console keys](https://console.groq.com/keys) |
| Cerebras | Fast inference experiments for short prototype loops | `free_fast` | `CEREBRAS_API_KEY` | [Inference docs](https://inference-docs.cerebras.ai/) |
| Mistral | First-party checks against Mistral model families | `free_reasoning` | `MISTRAL_API_KEY` | [Account setup](https://docs.mistral.ai/getting-started/quickstart/#account-setup) |

The bundled presets are intentionally conservative starter data, not a claim that a provider will
remain free, available, or quota-identical for every account. Provider catalogs, free tiers, and
rate limits move; `mpf doctor --live` is the truth test for your machine today.

Secondary routes worth adding once the first pool works: Google Gemini/Gemma, Cloudflare Workers AI,
GitHub Models, Hugging Face Inference Providers, and SambaNova. See
[`docs/PROVIDER_PRESETS.md`](./docs/PROVIDER_PRESETS.md) for the broader preset notes.

## Run one check, then ask the pool

After one provider key is configured, first prove that the route works:

```bash
mpf demo
```

Shape of the output:

```json
[
  {
    "id": "demo-ok",
    "passed": true,
    "failures": [],
    "text": "ok"
  }
]
```

Then ask a real one-off prompt with a single routed model call. Text output streams by default:

```bash
mpf ask "Write a poem about how ModelPreflight is the easiest way to try free LLM endpoints."
```

Shape of the output:

```text
ModelPreflight finds the route,
checks the key, and sends it out...
```

Use `pro` when the prompt is worth asking several times. It fans out cheap samples, synthesizes the
best answer through the judge group, and prints the final answer by default.

```bash
PROMPT=$(cat <<'PROMPT'
Write the strongest short pitch for ModelPreflight Pro Mode: explain why fanout
across cheap or free endpoints plus a judge pass is better than trusting one
brittle LLM call for a prototype decision. Include one caveat.
PROMPT
)

mpf pro "$PROMPT" \
  -n 8
```

Shape of the output:

```text
Pro Mode is useful when a prototype decision deserves more than one sample: fan out across cheap
or free routes, compare independent answers, then synthesize the strongest result through a judge
group...
```

The console stays focused on the final answer. Add `--artifact` when you want the prompt, routes,
candidate responses, candidate errors, group winners, and final judge output saved for inspection.

For structured-output work where you want to inspect all candidates:

```bash
PROMPT=$(cat <<'PROMPT'
Design three robust JSON schemas for extracting vendor name, renewal date,
total contract value, and termination notice from messy SaaS contracts. Include
failure modes.
PROMPT
)

mpf pro "$PROMPT" \
  -n 8 \
  --artifact .model-preflight/artifacts/schema-pro.json
```

For repeatable project checks, write JSONL smoke cases once and run:

```bash
mpf init-project
mpf run
```

`mpf demo` proves the configured route works. `mpf ask` is for a single one-off prompt. `mpf pro`
is for fanout plus synthesis. `mpf run` is for project-owned smoke files that should keep passing
as prompts, providers, and model slugs drift.

For the snappiest CLI startup, install once with `uv tool install model-preflight` or
`pipx install model-preflight`, then run `mpf ...` directly. `uv run mpf ...` may print package
sync messages before ModelPreflight starts.

---

<details>
<summary><img src="./docs/assets/readme-icons/info.svg" height="24" align="center" alt=""> <b>Why this repo exists</b></summary>

Early LLM prototypes often need a quick answer to a practical question: "Can this prompt, model group, or provider route work well enough to keep building?"

ModelPreflight gives you a lightweight layer for that stage:

- one global config for provider credentials and routing
- project-local JSONL smoke cases
- stable aliases such as `free_reasoning` and `free_fast`
- best-effort failover through LiteLLM
- audit records for live calls

</details>

<details>
<summary><img src="./docs/assets/readme-icons/check.svg" height="24" align="center" alt=""> <b>When to use it</b></summary>

Use ModelPreflight when:

- a prototype needs cheap LLM smoke checks before deeper eval work
- several projects should share the same local provider setup
- you want logical groups instead of hard-coding provider/model IDs everywhere
- provider quotas, model slugs, or dev-tier availability may drift
- you need enough provenance to debug "which model answered this?"

</details>

<details>
<summary><img src="./docs/assets/readme-icons/alert.svg" height="24" align="center" alt=""> <b>What it is not</b></summary>

ModelPreflight is not:

- a model leaderboard
- a formal benchmark framework
- a hosted inference gateway
- a provider catalog authority
- proof that an endpoint is free, fast, or available today

Bundled provider presets are starter data. Check each provider's current catalog and terms before relying on a route.

</details>

## 60-second start

```bash
uvx model-preflight --help

# In a persistent tool or project environment:
uv tool install model-preflight
# or:
pipx install model-preflight
```

Set one supported provider key, initialize, and run one live check:

```bash
export OPENROUTER_API_KEY=...
# or: export NVIDIA_NIM_API_KEY=...
# or: export GROQ_API_KEY=...
# or: export CEREBRAS_API_KEY=...
# or: export MISTRAL_API_KEY=...
mpf init
mpf doctor --live
mpf demo
```

Expected signal:

- `mpf init` writes your machine-local config for the first visible provider key. If no supported
  key is visible, it writes the OpenRouter starter config and tells you to export `OPENROUTER_API_KEY`.
- `mpf doctor --live` prints a deployments table, then `live check ok: group=...`.
- `mpf demo` prints JSON with `"passed": true` and an empty `"failures": []` list.

Add checks to a project:

```bash
cd my-project
mpf init-project
mpf run
```

Expected signal:

- `mpf init-project` writes `evals/smoke.jsonl`, writes `.model-preflight/README.md`, and updates `.gitignore`.
- `mpf run` prints JSON results for the starter cases. Every passing case has `"passed": true`.
- A failing case exits non-zero and includes strings under `"failures"` so you know what drifted.

Both `mpf` and `model-preflight` are installed as console scripts.

ModelPreflight catches missing keys, broken provider routes, prompt formatting regressions,
output-shape drift, accidental model/provider changes, and "this worked yesterday" prototype
failures before you wire the LLM call into something larger.

## No-key demo path

Use the minimal offline preset when you want to test the CLI and project workflow without a provider
account:

```bash
mpf init --preset minimal
mpf doctor --live
mpf demo
mpf init-project
mpf run
```

What this proves:

- Config loading works without secrets.
- The CLI can run a live-style check through the offline echo provider.
- Project bootstrap works by creating `evals/smoke.jsonl`.
- Smoke scoring works when `mpf run` returns JSON where every case has `"passed": true`.

What it does not prove: remote provider auth, quota, latency, or model quality. Use the OpenRouter
path below for that.

<details open>
<summary><img src="./docs/assets/readme-icons/route.svg" height="24" align="center" alt=""> <b>Install options</b></summary>

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

ModelPreflight reads provider routes and secret-source references from your OS-specific user config directory by default.
Use `mpf paths` to print the exact path. Override the path with either `--config` or
`MODEL_PREFLIGHT_CONFIG`.

```bash
mpf paths
mpf init
mpf doctor
mpf models
```

With no `--provider` or `--preset`, `mpf init` checks visible environment variables in this order:
`OPENROUTER_API_KEY`, `NVIDIA_NIM_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`,
`MISTRAL_API_KEY`. OpenRouter is only the fallback starter when none of those keys are visible.
Explicit `--provider` and `--preset` always override auto-detection.

Provider keys are not stored in the config. For local cross-project use, link a machine-local
dotenv file that stays outside this public package:

```bash
mpf setup --env-file /path/to/private/.env
```

Process env vars still win over linked dotenv values, which keeps CI and production behavior
compatible with standard secret injection.

Provider setup is discoverable from the CLI:

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

Use either primary path:

```bash
mpf setup --env-file /path/to/private/.env
mpf doctor --group free_reasoning --live

mpf init --provider openrouter
export OPENROUTER_API_KEY=...
mpf doctor --provider openrouter --live
```

For agent and CI readiness checks, make sure provider keys are visible in the agent process
environment or through a linked machine-local secret source, then use JSON diagnostics:

```bash
mpf doctor --group free_reasoning --json
```

`status: "ok"` means config and required keys are present. `error_code` distinguishes
`MISSING_REQUIRED_ENV`, `GROUP_NOT_FOUND`, and disabled matching provider/group cases.

| Provider | Best for | Env var | Setup |
|----------|----------|---------|-------|
| NVIDIA Build / NIM | Primary high-capability open/open-weight endpoint pool | `NVIDIA_NIM_API_KEY` | [API keys](https://build.nvidia.com/settings/api-keys) |
| OpenRouter | One-key first run with broad model access | `OPENROUTER_API_KEY` | [Authentication docs](https://openrouter.ai/docs/api-reference/authentication) |
| Groq | Fast repeated calls after first-run setup works | `GROQ_API_KEY` | [Groq console](https://console.groq.com/keys) |
| Cerebras | Fast inference experiments when current dev-tier limits fit | `CEREBRAS_API_KEY` | [Cerebras inference docs](https://inference-docs.cerebras.ai/) |
| Mistral | First-party Mistral model-family smoke checks | `MISTRAL_API_KEY` | [Mistral API keys](https://docs.mistral.ai/getting-started/quickstart/#account-setup) |

Secondary/overflow pool to add manually once the primary pool works: Google Gemini/Gemma,
Cloudflare Workers AI, GitHub Models, Hugging Face Inference Providers, and SambaNova. These are
documented in [`docs/PROVIDER_PRESETS.md`](./docs/PROVIDER_PRESETS.md), but not packaged as
first-run presets yet because auth shape, model IDs, and free/dev limits are more account-specific.

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

<details>
<summary><img src="./docs/assets/readme-icons/settings.svg" height="24" align="center" alt=""> <b>Provider preset discipline</b></summary>

Provider presets are best-effort starter data, not authoritative claims about free availability.

- user-local config wins over bundled defaults
- `mpf doctor` fails fast when required keys are missing
- optional/disabled providers do not block first-run checks
- live checks should be opt-in in CI
- endpoint names, quotas, pricing, and behavior can change without this repo knowing

See [`docs/PROVIDER_PRESETS.md`](./docs/PROVIDER_PRESETS.md) for the preset rules.

</details>

<details>
<summary><img src="./docs/assets/readme-icons/grid.svg" height="24" align="center" alt=""> <b>Custom config path</b></summary>

```bash
mpf init --config ./model-preflight.yaml
mpf doctor --config ./model-preflight.yaml
mpf doctor --config ./model-preflight.yaml --live

export MODEL_PREFLIGHT_CONFIG="$PWD/model-preflight.yaml"
mpf models
```

Use environment variables for secrets. Do not commit provider keys.

If you use 1Password, see [`docs/secrets/1password.md`](docs/secrets/1password.md)
for linked dotenv and `op run` examples. Run `mpf init --provider <provider>` once to create
the machine-local provider config.

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
mpf run
# or:
mpf run path/to/smoke_cases.jsonl
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

## Ask

`mpf ask` sends one prompt through one configured model group and prints the model text to stdout.
Plain text streams as tokens arrive. Progress and route metadata go to stderr by default, so stdout
stays clean for pipes and command substitution. In an interactive terminal, stderr status lines are
styled and separated from the answer by a blank line. Use `--quiet` to suppress all stderr status
lines, or `--hide-route` to hide provider/model route metadata while keeping progress visible. JSON
output is buffered so it remains valid JSON and includes route metadata unless `--hide-route` is set.

```bash
PROMPT="Write a poem about how ModelPreflight is the easiest way to use free LLM endpoints."

mpf ask "$PROMPT"
mpf ask "Write a shell-safe tagline" --quiet
mpf ask "Which model route is this using?"
mpf ask "Keep route metadata hidden, but show progress" --hide-route
mpf ask "Summarize why free endpoint preflight matters" --no-stream
mpf ask "Return JSON only: {\"ok\": true}" --group free_reasoning --json
```

Use `ask` for quick manual checks, demos, and shell snippets. Use `run` when the same prompt should
become a repeatable smoke case.

---

## Pro Mode

`mpf pro` fans out a one-off prompt, then synthesizes a final answer through a judge group.
By default, stdout contains only the final synthesized answer. Diagnostics go to stderr. Use
`--json` to print the full candidate payload, or `--artifact` to save it while keeping the console
focused on the final answer.

```bash
PROMPT=$(cat <<'PROMPT'
Use fanout plus synthesis to choose a robust JSON schema strategy for extracting
renewal terms from messy SaaS contracts. Return the final schema, validation
rules, and the main failure mode.
PROMPT
)

mpf pro "$PROMPT" \
  -n 8
```

Defaults:

| Option | Default | Role |
|--------|---------|------|
| `--n`, `-n` | `8` | number of sampled answers |
| `--sample-group` | configured default group | fanout group |
| `--judge-group` | configured default group | synthesis group |
| `--artifact path/to/pro.json` | unset | write prompt, routes, candidates, group winners, and final answer to a JSON artifact |
| `--json` | `false` | print full candidate payload to stdout instead of only the final answer |

`mpf pro` prints route/progress diagnostics to stderr before the fanout starts:

```text
[mpf] pro fanout n=2 sample_group=free_reasoning judge_group=free_reasoning
[mpf] sample nvidia: nvidia_nim/nvidia/nemotron-3-super-120b-a12b
[mpf] sample openrouter: openrouter/nvidia/nemotron-3-super-120b-a12b:free
[mpf] pro candidates ok=2/2
```

For post-run inspection:

```bash
mpf pro "Compare three prompt strategies for this extraction task" \
  -n 4 \
  --artifact .model-preflight/artifacts/pro-run.json
```

If every sample fails or returns empty text, the CLI exits non-zero and prints the first candidate
errors instead of showing a Python traceback. The full candidate list is still available through
`--artifact`.

<details>
<summary><img src="./docs/assets/readme-icons/lightning.svg" height="24" align="center" alt=""> <b>Cost and quota note</b></summary>

Fanout multiplies live provider calls. Keep `--n` low while testing, use restricted provider keys where available, and review provider dashboards when running against paid endpoints.

ModelPreflight records audit rows for live calls, but it does not enforce provider billing limits beyond your configured routing and provider-side controls.

</details>

---

## Library usage

```python
from model_preflight import ModelGateway, load_config, pro_mode

config = load_config()
gateway = ModelGateway(config)

print(gateway.text("Return only: ok", group="free_reasoning"))

result = pro_mode(
    gateway,
    "Solve this toy puzzle",
    n=8,
    sample_group=config.router.default_group,
    judge_group=config.router.default_group,
)
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
mpf init --provider openrouter
mpf doctor --live
mpf demo
mpf ask "write a tiny launch blurb for ModelPreflight"
mpf init-project
mpf run
mpf providers list
mpf providers guide openrouter
mpf models
mpf pro "solve this toy task" \
  -n 4 \
  --artifact .model-preflight/artifacts/pro-run.json
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

## For coding agents

Use these deterministic commands before changing provider routes, README examples, or release
surface docs:

```bash
uv sync
uv run pytest tests/test_readme_quality.py
uv run pytest
uv run ruff check .
uv run mypy src
```

README verification should pass before release-oriented README edits land. The focused README check
asserts that the first success path stays above the endpoint map, media URLs remain package-registry
safe, provider claims include a review date, and agent-facing commands stay discoverable.

Stable public paths:

| Path | Use |
|------|-----|
| [`README.md`](./README.md) | landing page, quickstart, and navigation hub |
| [`docs/quickstart.md`](./docs/quickstart.md) | deeper first-run walkthrough |
| [`docs/troubleshooting.md`](./docs/troubleshooting.md) | recovery steps after failed checks |
| [`docs/PROVIDER_PRESETS.md`](./docs/PROVIDER_PRESETS.md) | provider preset notes and drift warnings |
| [`docs/release-verification.md`](./docs/release-verification.md) | release and package-rendering checks |

Do not copy private specs, non-public provider/account names, internal URLs, or private agent protocol
files into this public repository. Use environment variables or user-local config for secrets.

---

## Design principles

- Global provider routing lives in the path printed by `mpf paths`.
- Project-local checks define cases, scoring, fixtures, and artifacts.
- LiteLLM handles provider-specific API quirks.
- ModelPreflight adds stable aliases, lightweight failover, and audit logs.
- Deterministic tests should run before live provider checks.

For the product scope and non-goals, see [`docs/NORTHSTAR.md`](./docs/NORTHSTAR.md).
