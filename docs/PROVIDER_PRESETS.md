# Provider Presets

Provider presets are best-effort starter data, not authoritative claims about free availability.

Rules:

- Bundled presets are conservative defaults.
- User-local config always wins over bundled presets.
- `mpf doctor` should fail fast when required keys are missing.
- Live provider checks should be opt-in in CI.
- Any free/dev endpoint may disappear, rate-limit, or change model behavior.

A provider row should include enough provenance to debug drift:

```yaml
name: groq_gpt_oss_120b
group: free_fast
model: groq/openai/gpt-oss-120b
api_key_env: GROQ_API_KEY
rpm: 10
tier: fast
last_verified: "2026-04-27"
status: best_effort
```
