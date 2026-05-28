# Compatibility and Deprecation Policy

ModelPreflight follows semantic versioning for the public Python package.

## Compatibility Scope

Stable compatibility covers:

- documented CLI commands and options;
- documented Python library entry points;
- smoke manifest fields documented in this repository;
- audit artifact fields documented in this repository.

Compatibility does not cover:

- provider-side pricing, quotas, catalog entries, or model behavior;
- provider preset recommendations after their documented review date;
- private or underscored Python symbols;
- terminal formatting details intended only for human display.

## Deprecation Policy

- Breaking changes require a major version unless they fix a security issue or a severe correctness bug.
- Deprecated public behavior should warn for at least one minor release before removal.
- Release notes must call out removed options, changed defaults, and audit/schema changes.
- Provider presets may change in minor releases when upstream providers change availability, quota, or API behavior.

## Provider Claim Freshness

Provider and model claims are best-effort snapshots. Every provider preset or provider-specific doc should include enough context for users to verify the current upstream catalog, pricing, quota, and terms before relying on it in CI or production workflows.
