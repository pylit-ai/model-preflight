# AGENTS.md

## Repository Boundary

This is the public ModelPreflight package repository.

The sibling repository `../model-preflight-private` is a private enterprise overlay. Do not read from it, copy from it, reference it, or make this public repository depend on it unless the user explicitly asks to work on the private overlay.

Public-safe content belongs here:

- package source under `src/model_preflight/`;
- public examples, tests, and documentation;
- generic agent instructions that are safe to publish;
- extension points that make private overlays unnecessary.

Private content does not belong here:

- enterprise/customer/internal code or docs;
- private provider routing, account names, private URLs, or secrets;
- generated private agent adapters;
- private specs, policies, or metactl projection state;
- overlay patches or files sourced from `../model-preflight-private`.

## Required Checks

Before committing public changes, run:

```bash
scripts/check_public_boundary.sh
uv run pytest
```

If a requested change seems private or ambiguous, keep it out of this repo and work from `../model-preflight-private` instead.
