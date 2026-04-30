#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  printf 'public boundary check failed: %s\n' "$1" >&2
  exit 1
}

if git ls-files | grep -E '(^|/)(\.claude|\.codex|\.cursor|\.gemini|\.metactl|\.omc|specs|overlays)(/|$)' >/dev/null; then
  fail "private/generated agent or overlay paths are tracked in the public repo"
fi

if git ls-files | grep -E '^(AGENTS\.md|CLAUDE\.md|GEMINI\.md)$' >/dev/null; then
  fail "root agent protocol files are intentionally private-only for this package"
fi

if git ls-files | grep -E '(^|/)(AGENTS\.local\.md|CLAUDE\.local\.md|GEMINI\.local\.md|metactl\.lock\.json|metactl\.yaml|opencode\.json)$' >/dev/null; then
  fail "local/private adapter files are tracked in the public repo"
fi

if git ls-files -o --exclude-standard | grep -E '(^|/)(\.claude|\.codex|\.cursor|\.gemini|\.metactl|\.omc|specs|overlays)(/|$)' >/dev/null; then
  fail "private/generated agent or overlay paths are present as untracked public files"
fi

if git ls-files -o --exclude-standard | grep -E '^(AGENTS\.md|CLAUDE\.md|GEMINI\.md)$' >/dev/null; then
  fail "root agent protocol files are present as untracked public files"
fi

if git grep -n -E 'customer-specific|internal-only|enterprise-only|proprietary overlay|proprietary agent|private provider|private overlay' -- ':!.gitignore' ':!scripts/check_public_boundary.sh' >/tmp/model-preflight-public-boundary.$$; then
  cat /tmp/model-preflight-public-boundary.$$ >&2
  rm -f /tmp/model-preflight-public-boundary.$$
  fail "private/internal overlay references found outside allowed public boundary docs"
fi
rm -f /tmp/model-preflight-public-boundary.$$

printf 'public boundary check passed\n'
