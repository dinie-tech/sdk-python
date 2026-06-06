# Changelog

All notable changes to the `dinie` Python SDK are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffold: `pyproject.toml` (PEP 621, hatchling build backend, `httpx>=0.27`
  as the sole runtime dependency, `requires-python = ">=3.10"`).
- `dinie/__init__.py` with `__version__ = "0.5.0"` (C-COLO-2: User-Agent source of truth).
- `dinie/py.typed` marker (PEP 561 — C-COLO-1; declared in wheel `force-include`).
- `dinie/runtime/` and `dinie/generated/` package stubs (C-COLO-3: directories precede
  first `generate --target python` run).
- `CODEOWNERS` boundary: `runtime/` → human owners, `generated/` → `@dinie-sdk-bot`.
- CI workflow (`ci.yml`): `ruff check`, `ruff format --check`, `mypy --strict dinie/`,
  `pytest` on Python 3.10, 3.11, 3.12. DoD-C2 gate — green from scaffold.
- Publish workflow stub (`publish.yml`): PyPI publishing deferred to V1.0; uses OIDC
  Trusted Publishing pattern (no static credentials).
- Smoke test (`tests/test_smoke.py`): `import dinie; assert __version__` — trivial green gate.
- MIT license.
