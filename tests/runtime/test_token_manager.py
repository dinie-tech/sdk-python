"""Tests for dinie.runtime.token_manager.

Uses pytest-httpx to intercept the POST /auth/token call without touching
the network.
"""

from __future__ import annotations

import threading
import time

import httpx
import pytest
from pytest_httpx import HTTPXMock

from dinie.runtime.errors import AuthenticationError
from dinie.runtime.token_manager import TOKEN_PATH, TokenManager

BASE_URL = "https://api.dinie.com.br"


def _make_manager(httpx_mock: HTTPXMock) -> TokenManager:
    client = httpx.Client()
    return TokenManager(
        client_id="id",
        client_secret="secret",
        base_url=BASE_URL,
        http_client=client,
    )


def _token_response(token: str = "tok-abc", expires_in: int = 3600) -> dict[str, object]:
    return {"access_token": token, "expires_in": expires_in, "token_type": "Bearer"}


class TestTokenManagerFetch:
    def test_fetches_token_on_first_access(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json=_token_response("tok-first"),
        )
        manager = _make_manager(httpx_mock)
        with httpx.Client() as client:
            manager._http_client = client
            token = manager.token
        assert token == "tok-first"

    def test_caches_token(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json=_token_response("tok-cached"),
        )
        with httpx.Client() as client:
            manager = TokenManager(
                client_id="id", client_secret="secret", base_url=BASE_URL, http_client=client
            )
            t1 = manager.token
            t2 = manager.token  # Should NOT trigger a second request
        assert t1 == t2 == "tok-cached"
        # Only 1 POST should have been made
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

    def test_invalidate_triggers_refresh(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json=_token_response("tok-1"),
        )
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json=_token_response("tok-2"),
        )
        with httpx.Client() as client:
            manager = TokenManager(
                client_id="id", client_secret="secret", base_url=BASE_URL, http_client=client
            )
            t1 = manager.token
            manager.invalidate()
            t2 = manager.token
        assert t1 == "tok-1"
        assert t2 == "tok-2"

    def test_auth_error_propagates(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            status_code=401,
            json={"detail": "invalid credentials"},
        )
        with httpx.Client() as client:
            manager = TokenManager(
                client_id="bad", client_secret="cred", base_url=BASE_URL, http_client=client
            )
            with pytest.raises(AuthenticationError):
                _ = manager.token

    def test_missing_access_token_raises(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json={"expires_in": 3600},  # no access_token
        )
        from dinie.runtime.errors import ApiError

        with httpx.Client() as client:
            manager = TokenManager(
                client_id="id", client_secret="s", base_url=BASE_URL, http_client=client
            )
            with pytest.raises(ApiError):
                _ = manager.token

    def test_missing_expires_in_uses_default(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json={"access_token": "tok"},
        )
        with httpx.Client() as client:
            manager = TokenManager(
                client_id="id", client_secret="s", base_url=BASE_URL, http_client=client
            )
            token = manager.token
        assert token == "tok"
        assert manager._expires_at > time.monotonic()


class TestTokenManagerConcurrency:
    def test_single_flight(self, httpx_mock: HTTPXMock) -> None:
        """Only one network call is issued when multiple threads race."""
        httpx_mock.add_response(
            url=f"{BASE_URL}{TOKEN_PATH}",
            method="POST",
            json=_token_response("tok-concurrent"),
        )
        with httpx.Client() as client:
            manager = TokenManager(
                client_id="id", client_secret="s", base_url=BASE_URL, http_client=client
            )
            results: list[str] = []
            errors: list[Exception] = []

            def fetch() -> None:
                try:
                    results.append(manager.token)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=fetch) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

        assert not errors
        assert all(r == "tok-concurrent" for r in results)
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
