# Changelog

All notable changes to the `dinie-sdk` Python SDK are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-06-13

## [1.0.0] - 2026-06-12

Initial public release.

### Added

- **Distribution name:** `dinie-sdk` on PyPI (`from dinie import Dinie` unchanged).
- **OIDC Trusted Publishing:** `publish.yml` — keyless PyPI publish via
  `pypa/gh-action-pypi-publish` (no `PYPI_API_TOKEN`). Triggered on `v*` tag push.
- **Tag automation:** `tag-release.yml` — pushes `vX.Y.Z` tag (via GitHub App token, D9)
  on merge of a `generator-bump`-labelled PR so `publish.yml` fires automatically.
- **Drift gate:** `ci.yml` drift job — hermetic check against `sdk-generator` vendored
  golden; fails CI on any hand-edit to `dinie/generated/`.
- **User-Agent header:** `Dinie-SDK-Python/<version> (api-version=<api_version>;
  python/<rt>)` injected on every request. `sdk_version` from
  `importlib.metadata.version("dinie-sdk")`; `api_version` from the generated
  `_API_VERSION` constant — neither is hardcoded.
- **`__version__`** derived from installed package metadata via
  `importlib.metadata.version("dinie-sdk")`.
- Full runtime layer: token management (client credentials + session exchange),
  multipart/form-data transport, pagination, webhook extraction, structured errors
  (`ApiError`, `APIConnectionError`, `APITimeoutError`, `SessionTokenExpiredError`).
- Generated surface: `dinie/generated/` — all six resource classes (`credentials`,
  `customers`, `kyc_attachments`, `loans`, `offers`, `biometrics`), webhook event
  types, `_api_version.py`, `.metadata.json` provenance. Regenerated from real
  `dinie-tech/api-docs` spec (PR #21 — biometrics surface, pruned demo fields).
- `py.typed` marker (PEP 561).
- MIT license.
- CI: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` on Python 3.10,
  3.11, 3.12.
