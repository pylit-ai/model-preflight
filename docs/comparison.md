# ModelPreflight vs LiteLLM vs promptfoo vs Langfuse

ModelPreflight sits before heavier eval, gateway, and observability tools. Its job is narrow:
check whether a cheap/free-ish provider route works on this machine, with this key, before a
prototype depends on it.

| Tool | Best used for | What it owns | What ModelPreflight does instead |
|------|---------------|--------------|----------------------------------|
| ModelPreflight | Local route preflight, free/dev endpoint checks, project smoke cases | Provider presets, stable local groups, `mpf doctor --live`, JSONL smoke cases, local audit records | Stays small and local; verifies first-run readiness before deeper tooling |
| LiteLLM | Provider abstraction, proxy/gateway, unified model calling | Normalized provider APIs, routing, gateway features | Uses LiteLLM underneath; adds first-run presets, smoke cases, and audit-oriented CLI workflow |
| promptfoo | Prompt, agent, and RAG evaluation/red-team workflows | Eval matrices, assertions, datasets, reports, CI evaluation | Runs lighter preflight checks before formal evals are worth configuring |
| Langfuse | LLM observability, tracing, prompt management, datasets, eval operations | Hosted/self-hosted observability platform and production feedback loop | Produces local proof that a route works before a prototype graduates to observability |

## Use Together

- Use `mpf doctor --live` before wiring a route into a prototype or coding-agent workflow.
- Keep `mpf run` smoke cases in projects where provider/model drift would break demos or CI.
- Move to promptfoo when you need comparative eval suites or red-team coverage.
- Move to Langfuse or another observability stack when production traces and feedback loops matter.
- Use LiteLLM directly when you need gateway behavior rather than a preflight CLI.

## Non-Goals

ModelPreflight is not a benchmark suite, hosted gateway, provider catalog authority, or guarantee
that any endpoint will remain free, fast, or available. Provider catalogs, free tiers, and rate
limits move; live preflight checks make that drift visible.
