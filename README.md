# dinie

Official Python SDK for the [Dinie](https://dinie.com.br) V3 API (backend-only).

A synchronous Python client for the Dinie credit-as-a-service platform: OAuth2
client-credentials auth (handled for you), automatic retries with idempotency, cursor
pagination, typed errors, and webhook verification. Snake_case throughout — the wire and
the Python surface match, so there is no casing to translate.

> **Status — pre-release (`0.5.0`).** The public surface is being generated from the Dinie
> V3 contract. PyPI publishing is planned for V1.0; until then install directly from the
> repository.

## Requirements

- Python >= 3.10
- A Dinie API credential (`client_id` + `client_secret`)

## Installation

```bash
pip install -e ".[dev]"
```

## Quickstart

```python
import dinie

client = dinie.Dinie(client_id="dinie_ci_…", client_secret="…")

customer = client.customers.create(
    email="ana@example.com",
    phone="+5511999999999",
    cpf="123.456.789-09",
)

customer.id      # "cust_…"
customer.status  # "pending_kyc"
```

> **Note:** the `Dinie` client and generated resource methods are populated in story 007.
> This scaffold ships a typed skeleton that keeps CI green.

The client owns an in-memory OAuth2 token cache, so **construct it once and reuse it**.
Tokens are fetched and refreshed transparently.

## Development

```bash
pip install -e ".[dev]"
pytest tests/
ruff check dinie/ tests/
mypy --strict dinie/
```

## Architecture

```
dinie/
  runtime/    # hand-written: HTTP, auth, retries, pagination, errors, webhooks
  generated/  # spec-driven: client, resources, types, events (emitted by sdk-generator)
```

The `runtime/` layer is hand-written and owned by humans. The `generated/` layer is
emitted by `sdk-generator --target python` from the OpenAPI spec + `sdk-config.yml`.
Never hand-edit `generated/` — regenerate instead.

## License

MIT
