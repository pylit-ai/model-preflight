# Eval Provenance

ModelPreflight is for prototype preflight checks, not formal benchmarking. Still, every live call should be auditable.

Log at least:

- timestamp
- logical group
- resolved provider/model if returned by provider
- prompt/case id
- generation params
- latency
- token usage when available
- artifact path

Do not use rotating provider pools for publishable eval claims unless the experiment explicitly studies ensemble/routing behavior.
