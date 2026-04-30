# Verification Status Report

## 1. Metadata

| Field | Value |
|-------|-------|
| Task | ModelPreflight first-run UX and release readiness |
| Timestamp | 2026-04-30T00:00:00Z |
| Branch | `main` |
| Commit | `c0396cc` |
| Overall status | `READY_WITH_LIVE_EVIDENCE` |

## 2. Executive status

All offline MUST_PASS gates are green. The implementation adds provider-scoped presets, smarter
doctor behavior, opt-in live checks, demo/project onboarding, provider guidance, audit metadata,
partial Pro Mode failure handling, light imports, tests, and docs.

Remote OpenRouter and NVIDIA live validation were verified from a private, gitignored environment
on 2026-04-30. Public artifacts record only pass/fail status and provider names; private
credentials, account details, prompts beyond the packaged demo, and raw transcripts are not
versioned here.

## 3. Objective precedence map

| Layer | Source | Effect |
|-------|--------|--------|
| Hard constraints | Repo non-goals in `docs/NORTHSTAR.md` | Keep package local-first; do not become a hosted gateway or provider catalog authority. |
| Project objective | `docs/first-run-ux-contract.md` | One provider, one key, one successful check before advanced config. |
| Release gate | `docs/release-verification.md` | Offline verifiers must pass; live provider checks remain optional diagnostics without credentials. |
| Session objective | User request | Implement, test, verify, and update docs. |

## 4. Axis readiness dashboard

```text
Axis                         Score   Evid.  Cap   Status        Top limiter
First-run UX behavior        ███████████████████░  95%   5/5   95%   PASS          provider facts are best-effort
Automated verification       ████████████████████ 100%   4/4  100%   PASS          none
Documentation alignment      ██████████████████░░  90%   4/4   95%   PASS          provider facts are best-effort
Live provider evidence       ██████████████████░░  90%   2/2   90%   PASS          live behavior can drift
Overall                      ███████████████████░  95%         95%   READY_WITH_LIVE_EVIDENCE
```

## 5. Gate ledger

| Gate | Requirement | Priority | Status | Tier | Evidence |
|------|-------------|----------|--------|------|----------|
| G-001 | Provider-scoped init writes one required OpenRouter deployment. | MUST_PASS | PASS | V1 | `tests/test_config_presets.py` |
| G-002 | No-key minimal path works end to end. | MUST_PASS | PASS | V1/V2 | CLI test plus temp-dir transcript |
| G-003 | Doctor required/optional semantics are actionable. | MUST_PASS | PASS | V1 | Config and CLI tests |
| G-004 | Demo/default run do not rely on source examples. | MUST_PASS | PASS | V1/V2 | CLI tests and stale-doc scan |
| G-005 | Lint/tests/typecheck/build pass. | MUST_PASS | PASS | V1 | Commands in evidence ledger |
| G-006 | Wheel includes preset YAML files. | MUST_PASS | PASS | V1 | Wheel zip inspection |
| G-007 | OpenRouter remote live check. | OPTIONAL_DIAGNOSTIC | PASS | V2 | Private-env command run, redacted public summary |
| G-008 | NVIDIA remote live check. | OPTIONAL_DIAGNOSTIC | PASS | V2 | Private-env command run, redacted public summary |

## 6. Evidence ledger

| Evidence | Command / artifact | Result |
|----------|--------------------|--------|
| E-001 | `uv run ruff check .` | PASS |
| E-002 | `uv run pytest -q` | PASS, 13 tests |
| E-003 | `uv run mypy src` | PASS |
| E-004 | `uv build` | PASS, wheel and sdist built |
| E-005 | Clean temp-dir minimal flow | PASS |
| E-006 | Wheel inspection for `model_preflight/presets/*.yaml` | PASS |
| E-007 | OpenRouter `init -> doctor --live -> demo` from private env | PASS |
| E-008 | NVIDIA `init -> doctor --live -> demo` from private env | PASS |

## 7. Regressions and blockers

No regressions found. No true blockers remain for package readiness.

Live-provider validation is intentionally not a public CI gate. It depends on private credentials
and provider/account state, so public docs should keep only high-level pass/fail evidence.

## 8. Loop closure queue

1. Promote wheel preset inspection into CI if package-data drift recurs.
2. Add structured JSON output for `doctor` and `providers` if agent consumers need machine parsing
   beyond exit codes.

## 9. Pressing questions

None.

## 10. Harness / instrumentation recommendations

- Convert `docs/release-verification.md` into a single script or Make target if the gate list grows.
- Keep live provider validation optional in CI unless a credentialed environment is explicitly
  provisioned.

## 11. Open risks

- Provider catalogs, pricing, and rate limits can drift outside repo control.
- Remote provider behavior can drift after verification because provider catalogs, accounts, quotas,
  and model availability are outside repo control.

## 12. Machine-readable state pointer

See `docs/status/verification_status_state.json`.
