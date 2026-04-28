# Model Selection

Model defaults are starter routes for smoke tests and method development. They are not benchmark
claims.

Verification date: 2026-04-28.

## Default choices

| Provider path | Default model | Why |
|---------------|---------------|-----|
| NVIDIA Build / NIM | `nvidia/nemotron-3-super-120b-a12b` | Primary high-capability NVIDIA-hosted open/open-weight route; NVIDIA documents the model in the NIM LLM API catalog. |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | Strong current free OpenRouter route with large context and free pricing. Better starter than older GPT-OSS defaults for general capability. |
| GroqCloud | `openai/gpt-oss-120b` | Still a good high-throughput Groq default: production model, fast, large context, explicit reasoning/tool support. |
| Cerebras | `gpt-oss-120b` | Still a good stable Cerebras default: production model; higher-capability preview alternatives have availability/deprecation caveats. |
| Mistral | `mistral-large-latest` | First-party Mistral route for broad reasoning checks on the Experiment tier. |

## Current better-than-GPT-OSS candidates

Prefer these for capability sweeps when available in your account:

- NVIDIA / OpenRouter: Nemotron 3 Super, Kimi K2 Thinking, Qwen3 Coder, MiniMax M2.5/M2.7.
- Cerebras: Z.ai GLM 4.7 or Qwen 3 235B for preview experiments, with rate-limit and deprecation checks.
- Google Gemini API: Gemma 4 for independent open-model family checks.

Keep GPT-OSS in the pool for stability and comparability. Do not treat it as the universal best
model.

## Eval discipline

- For development: rotate across provider/model pools to find method failures.
- For publishable claims: pin `provider`, `model`, date, params, endpoint, and route mode.
- Avoid random routers such as `openrouter/free` for claims unless routing randomness is the object
  of study.
- Re-run `mpf providers guide <provider>` and provider catalog checks before tagging a release.

