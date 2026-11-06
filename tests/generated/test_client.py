"""Tests for dinie.generated.client — the Dinie client's configuration defaults."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from dinie.generated.client import DEFAULT_BASE_URL, Dinie

PRODUCTION_BASE_URL = "https://api.dinie.com/api/v3"


def test_default_base_url_is_the_production_api() -> None:
    assert DEFAULT_BASE_URL == PRODUCTION_BASE_URL


def test_client_without_a_base_url_calls_production_for_both_token_and_resources(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DINIE_BASE_URL", raising=False)
    httpx_mock.add_response(
        url=f"{PRODUCTION_BASE_URL}/auth/token",
        method="POST",
        json={"access_token": "tok", "expires_in": 3600, "token_type": "Bearer"},
    )
    httpx_mock.add_response(
        url=f"{PRODUCTION_BASE_URL}/banks",
        method="GET",
        json={"id": "bank_1", "name": "Banco", "display_name": "Banco"},
    )

    bank = Dinie(client_id="id", client_secret="secret").banks.list()

    assert bank.id == "bank_1"
