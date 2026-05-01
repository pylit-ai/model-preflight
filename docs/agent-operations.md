# Agent operations

ModelPreflight is designed to be installed and operated by coding agents as well as humans. Give an
agent one of the prompts below when you want it to add route preflight checks to another repository.

## Why this shape

Current agent tooling favors small entrypoint instructions plus linked specs:

- OpenAI Codex uses `AGENTS.md` as repository instructions, and OpenAI describes `AGENTS.md` as a
  table of contents rather than a giant knowledge base.
- The AGENTS.md format describes itself as a README for agents with dev-environment and testing
  instructions.
- GitHub Copilot supports repository instructions, path-specific instructions, and `AGENTS.md`.
- Claude Code uses `CLAUDE.md`, custom commands, hooks, skills, and MCP.
- Gemini CLI supports `GEMINI.md`, imports, memory commands, and custom command TOML files.
- Symphony-style workflows show the emerging pattern: a self-contained Markdown spec with optional
  YAML front matter, then a prompt that tells an agent to implement or run the spec.

Sources checked 2026-05-01:

- [OpenAI Codex AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [OpenAI harness engineering](https://openai.com/index/harness-engineering/)
- [AGENTS.md format](https://github.com/agentsmd/agents.md)
- [GitHub Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- [Claude Code overview](https://code.claude.com/docs)
- [Claude CLAUDE.md guide](https://claude.com/blog/using-claude-md-files)
- [Gemini CLI GEMINI.md docs](https://geminicli.com/docs/cli/gemini-md/)
- [Gemini CLI custom commands](https://google-gemini.github.io/gemini-cli/docs/cli/custom-commands.html)
- [Cursor rules docs](https://docs.cursor.com/en/context/rules)
- [OpenAI Symphony spec](https://github.com/openai/symphony/blob/main/SPEC.md)

## Copy-paste prompt: prompt-based init

Use this when someone wants the agent equivalent of `mpf init` without learning every command first:

```text
Initialize ModelPreflight in this repository.

Goals:
- Add the smallest safe ModelPreflight setup for this repo.
- Use the no-key `minimal` preset first unless I have already provided a provider key.
- Keep provider keys, `.env` files, private account names, and internal URLs out of the repo.
- Add or refine project-local smoke cases only if this repo has obvious LLM prompts, agents,
  extraction tasks, or provider calls.

Suggested command path:
1. Detect the package manager and install or document `model-preflight` in the repo's style.
2. Run `mpf init --preset minimal`.
3. Run `mpf demo`.
4. Run `mpf init-project`.
5. Run `mpf run`.
6. If live credentials are already visible and live calls are appropriate, also run
   `mpf doctor --live`; otherwise report the exact env var needed.

Acceptance:
- No secrets are committed.
- A no-key validation path works or the exact failure is reported.
- Any smoke cases added are relevant to this repo, not generic placeholders.
- The final response lists files changed, commands run, validation status, and the next command for
  live provider validation.
```

## Copy-paste prompt: set up ModelPreflight

```text
Set up ModelPreflight in this repository using this public spec:

https://github.com/pylit-ai/model-preflight/blob/main/docs/agent-specs/setup-model-preflight.md

Do the smallest safe implementation. Keep provider secrets out of the repo. Prefer the no-key
minimal preset for local validation unless I provide a provider key. Add or update project-local
smoke cases that match this repo's actual LLM calls. Run the acceptance checks from the spec and
summarize exact files changed plus commands run.
```

## Copy-paste prompt: diagnose provider drift

```text
Diagnose ModelPreflight provider drift in this repository using this public spec:

https://github.com/pylit-ai/model-preflight/blob/main/docs/agent-specs/provider-drift-check.md

Do not rotate secrets or change billing-affecting provider settings. Use existing config and
environment only. If live credentials are missing, run no-key checks and report the exact minimal
env var needed for live validation.
```

## Tool-specific placement

Use these files in the target repository that consumes ModelPreflight, not necessarily in this
package repository:

| Tool | Lightweight entrypoint | Deeper reusable workflow |
|------|------------------------|--------------------------|
| Codex / many agents | `AGENTS.md` | link to `docs/agent-specs/setup-model-preflight.md` |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/instructions/model-preflight.instructions.md` |
| Claude Code | `CLAUDE.md` | custom command or skill that links this doc |
| Gemini CLI | `GEMINI.md` | `.gemini/commands/model-preflight/setup.toml` |
| Cursor | `AGENTS.md` or `.cursor/rules/*.mdc` | path-scoped rule for smoke files |

Keep auto-loaded files short. Put commands, acceptance criteria, and failure recovery in linked
docs or specs so agents can fetch only the workflow they need.

## Existing skill

This repo also ships [`skills/model-preflight/SKILL.md`](../skills/model-preflight/SKILL.md). Use it
when your agent runtime supports skill directories. The skill is intentionally small and points the
agent to deterministic commands instead of embedding the full docs.
