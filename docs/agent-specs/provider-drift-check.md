---
name: provider-drift-check
description: Diagnose whether configured ModelPreflight providers, model IDs, keys, and smoke cases still work.
---

# Provider drift check

## Objective

Find out whether a repository's configured LLM routes still work today, without changing secrets or
making unsupported provider claims.

## Safety rules

- Do not rotate, print, or commit provider secrets.
- Do not change provider billing settings.
- Do not hide failing live checks; report exact error codes and next actions.
- Use no-key checks when credentials are unavailable.

## Diagnostic steps

1. Inspect paths and config source:

   ```bash
   mpf paths
   mpf doctor --json
   mpf models
   ```

2. If credentials are present and live checks are allowed:

   ```bash
   mpf doctor --live
   mpf demo
   ```

3. If the project has smoke cases:

   ```bash
   mpf run
   ```

4. If a provider or model fails, check provider setup guidance:

   ```bash
   mpf providers list
   mpf providers guide openrouter
   mpf providers guide nvidia
   ```

## Failure interpretation

| Signal | Meaning | Next action |
|--------|---------|-------------|
| `MISSING_REQUIRED_ENV` | Selected route needs an env var that is not visible to this process. | Export the named key or link a private dotenv file. |
| `GROUP_NOT_FOUND` | The requested group is not configured. | Run `mpf models`, then select an existing group or update config. |
| `NO_READY_DEPLOYMENT` | The group exists, but no enabled deployment is usable. | Check required keys and disabled deployments. |
| Provider 401/403 | Auth changed or key lacks access. | Recreate or scope the key in the provider console. |
| Provider 404/model not found | Model slug or catalog changed. | Check provider docs and update local config. |
| Provider 429/unavailable | Quota/rate limit/availability issue. | Wait, reduce `-n`, or switch route/group. |

## Completion report

Return:

- config path used
- provider/group checked
- commands run and exit status
- live vs no-key validation status
- failing provider/model/error code
- one next command or config edit for the human
