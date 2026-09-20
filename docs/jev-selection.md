# Optional complete-answer selection

`mpf pro "your prompt" --jev-select` explicitly permits sending the prompt and
successful candidate answers to TypeSafe's paid Jev endpoint. Provision
`TYPESAFE_API_KEY` through your approved environment/secret workflow. Ordinary
`mpf pro` remains fanout plus synthesis with no TypeSafe request.

The selector asks one Choice question. It returns a supplied candidate verbatim,
including whitespace, only when that candidate is selected with confidence at
least 0.8. `needs_synthesis`, `none_adequate`, low confidence, missing credentials,
invalid responses, and transport failures retain the existing synthesis workflow.
Confidence describes Jev's distribution, not a calibrated correctness guarantee.
This opt-in pilot has no measured quality or cost advantage yet.

Controls: `--jev-model` defaults to pinned `jev-1.13.0`, `--jev-timeout` defaults
to 10 seconds (maximum 30, per blocking network operation), and
`--jev-min-confidence` defaults to 0.8. There is one request and no retries or
redirects. Payloads above 96 KB, responses above 64 KB, or over 253 candidates
fall back. Existing sample and synthesis provider calls retain their own costs.

Python callers opt in with `pro_mode(gateway, prompt, jev_select=True)` and can
set `jev_model`, `jev_timeout`, and `jev_min_confidence`. JSON and explicitly
requested artifacts include selection/fallback metadata, requested/returned model,
and validated reported token usage when available. Missing usage is not zero cost.
No raw TypeSafe response or transport error is logged. Existing artifacts contain
prompts and candidates: keep them private as before. Do not submit secrets.

Pinned model requests require an exact returned-model match; mismatch falls back
while retaining validated returned-model and usage metadata. Only explicitly
requested `jev-latest` and `jev-preview` aliases allow a different returned version.
Every selector decision reports attempted request count (zero or one) and elapsed
seconds, including preflight and transport fallbacks, to expose selection overhead.

Contract checked against <https://docs.typesafe.ai/api> and
<https://docs.typesafe.ai/models> on 2026-09-19. The selection rubric lives in
`src/model_preflight/jev.py`. Downstream answer quality still needs private pilot
evaluation before relying on this route broadly.
