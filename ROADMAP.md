# Roadmap

This roadmap is directional, not a promise of delivery dates.

## Now

- Keep the local CLI and Python library small, inspectable, and Apache-2.0.
- Improve first-run setup, offline scoring, audit artifacts, and provider failure handling.
- Maintain public provider preset examples with dated review metadata and clear drift warnings.
- Keep tests deterministic by default; live provider checks must remain opt-in.

## Next

- Add stronger CI examples for smoke checks and artifact upload.
- Improve `mpf doctor --json` output for automation and support workflows.
- Expand provider preset contribution templates without turning presets into pricing or availability claims.
- Publish compatibility and deprecation notes with each minor release.

## Later

- Evaluate team artifact history, provider drift alerts, and hosted dashboards only after repeated external demand.
- Consider richer SDKs or protocol docs when real users need stable extension points.
- Consider enterprise controls only after the local workflow proves sustained usage.

## Non-Goals

- Public pricing oracle.
- Formal model benchmark suite.
- Hosted gateway in the local package.
- Customer prompt, trace, or artifact collection in the OSS repo.
