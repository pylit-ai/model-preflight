# Contributing

Keep the project small. Good contributions improve first-run setup, provider-failure handling, provenance, docs, or offline test coverage.

Avoid adding heavyweight benchmark logic, hosted-service assumptions, or hard-coded claims about free endpoint availability.

## Certificate of Origin

This project uses the Developer Certificate of Origin instead of a CLA.

Add a signoff to each commit:

```bash
git commit -s
```

The signoff certifies that you wrote the contribution, have the right to submit it, or are passing along a contribution under a compatible open source license. See <https://developercertificate.org/> for the full DCO text.

## Compatibility

Public CLI behavior, documented Python APIs, smoke manifest fields, and audit artifact fields should follow the compatibility policy in [docs/compatibility.md](./docs/compatibility.md).

Breaking changes need release-note coverage. Provider preset updates should include review context because provider catalogs, pricing, quota, and behavior can drift outside this repository.

## Provider Claims

Do not add stable claims about model quality, benchmark rank, price, quota, or long-term free-tier availability. If a provider note is useful, include enough context for users to verify it against the provider's current docs or console.
