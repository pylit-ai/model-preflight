# What ModelPreflight Is

ModelPreflight is a local developer tool for cheap, repeatable LLM smoke checks before teams spend more time or money on a model route.

It helps users:

- run small prompt smoke cases against configured providers;
- compare basic pass/fail behavior across candidate routes;
- keep audit metadata for prototype decisions;
- catch provider setup, credential, routing, and regression problems early;
- integrate local checks into agent and CI workflows.

# What ModelPreflight Is Not

ModelPreflight is not:

- a formal benchmark framework;
- a model leaderboard;
- a pricing, quota, or provider availability oracle;
- a hosted model gateway;
- a replacement for security, privacy, or compliance review;
- a claim that any provider model is open source.

Provider catalogs, pricing, quotas, free tiers, model behavior, and terms can change outside this repository. Verify current provider facts before relying on any route in CI or production.
