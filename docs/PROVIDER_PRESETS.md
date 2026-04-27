# Provider Presets

Provider presets are best-effort starter data, not authoritative claims about free availability.

Rules:

- Bundled presets are conservative defaults.
- User-local config always wins over bundled presets.
- `mpf init --provider openrouter` is the preferred first-run remote preset.
- `mpf init --preset minimal` is the no-key offline preset for CLI/demo validation.
- `mpf doctor` should fail fast only when required keys for the selected group/provider are missing.
- Optional or disabled providers should be reported as skipped/warnings, not first-run failures.
- Live provider checks should be opt-in in CI.
- Any free/dev endpoint may disappear, rate-limit, or change model behavior.

A provider row should include enough provenance to debug drift:

```yaml
name: groq_gpt_oss_120b
provider: groq
group: free_fast
model: groq/openai/gpt-oss-120b
api_key_env: GROQ_API_KEY
enabled: false
required: false
rpm: 10
tier: fast
last_verified: "2026-04-27"
status: optional
```

Current packaged presets:

| Preset | Purpose | Required key |
|--------|---------|--------------|
| `minimal` | Offline/no-key CLI and project workflow validation | none |
| `openrouter` | One-provider first run | `OPENROUTER_API_KEY` |
| `multi-free-dev` | Advanced multi-provider starter with optional fast providers disabled | `OPENROUTER_API_KEY` |

Provider commands:

```bash
mpf providers list
mpf providers guide openrouter
mpf providers test openrouter
```
