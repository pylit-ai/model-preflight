# North Star

ModelPreflight makes it trivial to run cheap, provider-agnostic LLM smoke tests and quick prototype checks from any early-stage project.

The project optimizes for:

1. One-command setup.
2. One global provider config per machine.
3. Project-local smoke cases.
4. Best-effort free/dev endpoint routing.
5. Clear provenance for every live call.
6. Graceful degradation when providers, quotas, or model IDs change.

The project explicitly does not aim to be:

- a model leaderboard,
- a full benchmark framework,
- a hosted gateway,
- a provider catalog authority,
- or a replacement for rigorous evals.

If a feature makes first-run setup harder, requires frequent provider maintenance, or hides which model produced a result, it is probably out of scope.
