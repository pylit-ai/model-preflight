# Release Verification

Run the offline gate from the repository root:

```bash
uv run ruff check .
uv run pytest
uv build
```

Optional live evidence requires a provider key:

```bash
export OPENROUTER_API_KEY=...
tmpdir="$(mktemp -d)"
mpf init --provider openrouter --config "$tmpdir/config.yaml"
mpf doctor --config "$tmpdir/config.yaml" --live
mpf demo --config "$tmpdir/config.yaml"
```

Do not block local CI on provider credentials. Treat live transcripts as diagnostic release evidence
unless a release explicitly requires remote-provider validation.
