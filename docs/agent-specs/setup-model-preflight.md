---
name: setup-model-preflight
description: Add ModelPreflight to a repository and prove one local smoke path works without committing secrets.
---

# Set up ModelPreflight

## Objective

Add ModelPreflight to a target repository so a human or agent can check whether the current LLM
route works before wiring it into application code.

## Safety rules

- Do not commit provider keys, `.env` files, private account names, or internal URLs.
- Prefer `mpf init --preset minimal` for first validation when live credentials are absent.
- Do not claim provider price, quota, model availability, or benchmark quality as stable.
- Do not add live provider calls to default CI unless the repository owner explicitly asks for it.

## Implementation steps

1. Detect the project package manager and add `model-preflight` as a dev/tool dependency when that
   matches the project style. If unsure, document the command instead of forcing a dependency.
2. Run:

   ```bash
   mpf init --preset minimal
   mpf demo
   mpf init-project
   mpf run
   ```

3. Replace the starter smoke cases with 1-3 project-specific JSONL cases if the repo has obvious
   LLM prompts, agents, extraction tasks, or provider calls.
4. Keep provider config machine-local. Use `mpf setup --env-file /path/to/private/.env` only when
   the user provides a private env file path.
5. Add docs or README notes that point humans to:
   - `mpf ask` for one routed prompt
   - `mpf run` for repeatable smoke cases
   - `mpf doctor --live` for diagnostics
   - `mpf pro -n <count>` when sampling multiple candidates is worth the cost

## Acceptance checks

Run the strongest checks that are safe in the current environment:

```bash
mpf paths
mpf doctor --json
mpf demo
mpf run
```

If the target repo has tests or lint commands, run the relevant local checks after edits.

## Completion report

Return:

- files changed
- commands run and exit status
- whether validation used `minimal` or a live provider
- exact missing env vars if live validation could not run
- next command for the human to run with real credentials
