# AGENTS.md

## Repository Boundary

This is the public ModelPreflight package repository.

Do not add private, internal, customer-specific, enterprise-only, generated agent, or proprietary overlay material to this repository.

If a task appears to require private/internal material, stop and ask for the correct private workspace instead of guessing, searching sibling directories, or adding references here.

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
- private overlay patches or files.

## Required Checks

Before committing public changes, run:

```bash
scripts/check_public_boundary.sh
uv run pytest
```

If a requested change seems private or ambiguous, keep it out of this repo and ask for the correct private workspace.
