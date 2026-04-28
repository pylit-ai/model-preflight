# 1Password Secrets

ModelPreflight reads provider credentials from environment variables. 1Password
is optional; plain shell exports, `.env` loaders, CI secrets, and other secret
managers work as long as they provide the same env vars.

## Recommended Local Pattern

Use `op run` when you want secrets available only to a subprocess:

```bash
op run --env-file=.env.1password -- mpf smoke openrouter/auto --prompt "ping"
```

In `.env.1password`, use 1Password secret references:

```dotenv
OPENROUTER_API_KEY=op://model-preflight/env/OPENROUTER_API_KEY
GROQ_API_KEY=op://model-preflight/env/GROQ_API_KEY
```

## Optional Vault Bootstrap

The helper script can create or update a vault item from `.env.example` and a
local `.env`:

```bash
unset OP_SERVICE_ACCOUNT_TOKEN
op whoami --format json
python3 scripts/onepassword_env_secrets.py push --vault model-preflight --item env
```

Pull to local `.env` only when your workflow needs a materialized file:

```bash
python3 scripts/onepassword_env_secrets.py pull --vault model-preflight --item env
```

`.env` is gitignored. Do not commit revealed secret files.

## Service Accounts And CI

For local setup, prefer a human-authenticated `op` session. The helper refuses
service-account auth by default because service accounts may have narrower vault
permissions than expected.

For CI, prefer the CI platform's secret store or 1Password's CI integration with
least-privilege vault access. Do not bootstrap or rotate vaults from public CI.
