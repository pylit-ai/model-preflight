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

## Reasoning-route smoke trace example

For a known reasoning-capable route, use `free_reasoning` and parse the output JSON to capture reasoning/usage/error evidence:

```bash
tmpdir="$(mktemp -d)"
cat >"$tmpdir/config.yaml" <<'YAML'
provider: openrouter
routes:
  free_reasoning:
    provider: openrouter
    model: openrouter/free/gpt-4.1
YAML
cat >"$tmpdir/cases.jsonl" <<'JSON'
{"id":"reasoning-smoke-auth-fail","route":"free_reasoning","input":"Explain why smoke tests are useful in one short paragraph."}
JSON
uv run mpf init --provider openrouter --config "$tmpdir/config.yaml"
uv run mpf run "$tmpdir/cases.jsonl" --config "$tmpdir/config.yaml" > "$tmpdir/raw_smoke.json"

python - <<'PY'
import json

records = json.loads(open("$tmpdir/raw_smoke.json").read())
r = records[0] if isinstance(records, list) else records
sample = {
    "route": r.get("route"),
    "reasoning": r.get("reasoning"),
    "reasoning_details": r.get("reasoning_details"),
    "reasoning_summary": r.get("reasoning_summary"),
    "usage": r.get("usage"),
    "error": r.get("error"),
    "failures": r.get("failures", [])[:1],
    "status": r.get("status"),
}
print(json.dumps(sample, indent=2))
PY
```

A stored sample artifact to attach to a release note is:

- `docs/reasoning-smoke-trace-sample.json`

Example parsed output shape:

```json
{
  "route": "free_reasoning",
  "reasoning": null,
  "reasoning_details": null,
  "reasoning_summary": null,
  "usage": null,
  "error": "AuthenticationError: litellm.AuthenticationError: ... No cookie auth credentials found ...",
  "failures": [
    "provider exception: AuthenticationError: litellm.AuthenticationError: ..."
  ],
  "status": "failed"
}
```
