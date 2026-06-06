"""Tests for dinie.runtime.http — SyncHttpClient transport behaviour.

DoD coverage:
- DoD-R2: Authorization header present on every call
- DoD-R3: with_options() shares TokenManager + httpx.Client
- DoD-R4: 429→200 retries with same idempotency key; 409 NOT retried;
          Retry-After:120 capped at ≤60s; X-Dinie-Retry-Count:N on retries
- DoD-R5: 401→invalidate→retry (one-shot re-auth)

pytest-httpx is used for all HTTP interception — no real network calls.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from dinie.runtime.errors import (
    ApiError,
    ConflictError,
)
from dinie.runtime.http import (
    SyncHttpClient,
)
from dinie.runtime.token_manager import TOKEN_PATH, TokenManager

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

BASE_URL = "https://api.dinie.com.br"
TOKEN_URL = f"{BASE_URL}{TOKEN_PATH}"
API_URL = f"{BASE_URL}/v1/resource"


def _token_response(token: str = "test-token", expires_in: int = 3600) -> dict[str, object]:
    return {"access_token": token, "expires_in": expires_in, "token_type": "Bearer"}


@pytest.fixture()
def http_client() -> Iterator[httpx.Client]:
    with httpx.Client() as client:
        yield client


def _make_client(
    http_client: httpx.Client,
    httpx_mock: HTTPXMock,
    token: str = "test-token",
) -> SyncHttpClient:
    """Build a SyncHttpClient with a pre-seeded token."""
    httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response(token))
    manager = TokenManager(
        client_id="id", client_secret="secret", base_url=BASE_URL, http_client=http_client
    )
    client = SyncHttpClient(
        base_url=BASE_URL,
        max_retries=2,
        timeout=5.0,
        http_client=http_client,
        token_manager=manager,
    )
    return client


# -------------------------------------------------------------------------
# Basic request / authorization
# -------------------------------------------------------------------------


class TestBasicRequest:
    def test_get_success(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        """A successful GET returns the parsed JSON body."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(url=API_URL, method="GET", json={"id": "123"})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        result = client.request("GET", "/v1/resource")
        assert result == {"id": "123"}

    def test_authorization_header_sent(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """DoD-R2: every request carries Authorization: Bearer <token>."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("my-tok"))
        httpx_mock.add_response(url=API_URL, method="GET", json={})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        client.request("GET", "/v1/resource")

        api_request = httpx_mock.get_requests()[-1]
        assert api_request.headers["authorization"] == "Bearer my-tok"

    def test_204_returns_none(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(url=API_URL, method="DELETE", status_code=204)

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        result = client.request("DELETE", "/v1/resource")
        assert result is None

    def test_post_sends_body(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        from dinie.runtime.models import OMIT

        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource", method="POST", json={"created": True}
        )

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        client.request("POST", "/v1/resource", body={"name": "test", "optional": OMIT})

        api_req = httpx_mock.get_requests()[-1]
        import json

        sent_body = json.loads(api_req.content)
        assert sent_body == {"name": "test"}  # OMIT was stripped


# -------------------------------------------------------------------------
# Idempotency key
# -------------------------------------------------------------------------


class TestIdempotencyKey:
    def test_idempotency_key_on_post(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(url=f"{BASE_URL}/v1/resource", method="POST", json={"ok": True})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        client.request("POST", "/v1/resource", body={})

        api_req = httpx_mock.get_requests()[-1]
        assert "idempotency-key" in {k.lower() for k in api_req.headers.keys()}

    def test_get_has_no_idempotency_key(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(url=API_URL, method="GET", json={})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        client.request("GET", "/v1/resource")

        api_req = httpx_mock.get_requests()[-1]
        assert "idempotency-key" not in {k.lower() for k in api_req.headers.keys()}


# -------------------------------------------------------------------------
# DoD-R4: Retry behaviour
# -------------------------------------------------------------------------


class TestRetryBehaviour:
    def test_429_then_200_succeeds(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        """DoD-R4: 429 → 200 after 1 retry with the same idempotency key."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource",
            method="POST",
            status_code=429,
            headers={"Retry-After": "0"},
        )
        httpx_mock.add_response(url=f"{BASE_URL}/v1/resource", method="POST", json={"ok": True})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        with patch("dinie.runtime.http.time.sleep"):
            result = client.request("POST", "/v1/resource", body={})

        assert result == {"ok": True}

        # Both attempts carry the same idempotency key
        post_reqs = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/resource"]
        assert len(post_reqs) == 2
        key_first = post_reqs[0].headers.get("idempotency-key")
        key_second = post_reqs[1].headers.get("idempotency-key")
        assert key_first == key_second
        assert key_first is not None

    def test_retry_count_header_on_retry(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """DoD-R4: X-Dinie-Retry-Count:N injected on retry attempts."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource",
            method="POST",
            status_code=500,
        )
        httpx_mock.add_response(url=f"{BASE_URL}/v1/resource", method="POST", json={"ok": True})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        with patch("dinie.runtime.http.time.sleep"):
            client.request("POST", "/v1/resource", body={})

        post_reqs = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/resource"]
        # First attempt: no header
        assert "x-dinie-retry-count" not in {k.lower() for k in post_reqs[0].headers.keys()}
        # Second attempt: header = "1"
        assert post_reqs[1].headers.get("x-dinie-retry-count") == "1"

    def test_409_not_retried(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        """DoD-R4: 409 is NOT retried — it raises ConflictError immediately."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource",
            method="POST",
            status_code=409,
            json={"detail": "conflict"},
        )

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        with pytest.raises(ConflictError):
            client.request("POST", "/v1/resource", body={})

        post_reqs = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/resource"]
        assert len(post_reqs) == 1  # no retry

    def test_retry_after_120_capped_to_60(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """DoD-R4: Retry-After:120 is capped at ≤60s."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource",
            method="POST",
            status_code=429,
            headers={"Retry-After": "120"},
        )
        httpx_mock.add_response(url=f"{BASE_URL}/v1/resource", method="POST", json={"ok": True})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        sleep_calls: list[float] = []
        with patch("dinie.runtime.http.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
            client.request("POST", "/v1/resource", body={})

        assert sleep_calls
        assert sleep_calls[0] <= 60.0

    def test_max_retries_exceeded_raises(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """Exhausting the retry budget raises the last error."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        # 3 responses for initial + 2 retries
        for _ in range(3):
            httpx_mock.add_response(
                url=API_URL,
                method="GET",
                status_code=503,
            )

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        with patch("dinie.runtime.http.time.sleep"):
            with pytest.raises(ApiError) as exc_info:
                client.request("GET", "/v1/resource")
        assert exc_info.value.status == 503


# -------------------------------------------------------------------------
# DoD-R5: 401 one-shot re-auth
# -------------------------------------------------------------------------


class TestOneShot401:
    def test_401_triggers_invalidate_and_retry(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """DoD-R5: 401 → invalidate token → retry once, no backoff."""
        # First token fetch
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("tok-1"))
        # API returns 401
        httpx_mock.add_response(
            url=API_URL, method="GET", status_code=401, json={"detail": "expired"}
        )
        # Second token fetch (after invalidate)
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("tok-2"))
        # API succeeds with new token
        httpx_mock.add_response(url=API_URL, method="GET", json={"id": "ok"})

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=1,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        result = client.request("GET", "/v1/resource")
        assert result == {"id": "ok"}

        # Verify second API request used the new token
        api_reqs = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/resource"]
        assert api_reqs[0].headers["authorization"] == "Bearer tok-1"
        assert api_reqs[1].headers["authorization"] == "Bearer tok-2"

    def test_401_not_retried_twice(self, http_client: httpx.Client, httpx_mock: HTTPXMock) -> None:
        """Second consecutive 401 raises AuthenticationError."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("tok-1"))
        httpx_mock.add_response(
            url=API_URL, method="GET", status_code=401, json={"detail": "expired"}
        )
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("tok-2"))
        httpx_mock.add_response(
            url=API_URL, method="GET", status_code=401, json={"detail": "still expired"}
        )

        from dinie.runtime.errors import AuthenticationError

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )

        with pytest.raises(AuthenticationError):
            client.request("GET", "/v1/resource")


# -------------------------------------------------------------------------
# DoD-R3: with_options() sharing
# -------------------------------------------------------------------------


class TestWithOptions:
    def test_with_options_shares_token_manager(self, http_client: httpx.Client) -> None:
        """DoD-R3: with_options() clone shares the same TokenManager instance."""
        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        clone = client.with_options(max_retries=5)
        assert clone._token_manager is client._token_manager
        assert clone._http is client._http

    def test_with_options_overrides_defaults(self, http_client: httpx.Client) -> None:
        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=2,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        clone = client.with_options(timeout=99.0, max_retries=10)
        assert clone._default_timeout == 99.0
        assert clone._default_max_retries == 10
        assert clone._base_url == BASE_URL  # unchanged


# -------------------------------------------------------------------------
# Rate-limit header tracking
# -------------------------------------------------------------------------


class TestRateLimitTracking:
    def test_rate_limit_updated_from_response(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
        httpx_mock.add_response(
            url=API_URL,
            method="GET",
            json={},
            headers={
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "42",
                "x-ratelimit-reset": "120",
            },
        )

        manager = TokenManager(
            client_id="id", client_secret="s", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL,
            max_retries=0,
            timeout=5.0,
            http_client=http_client,
            token_manager=manager,
        )
        client.request("GET", "/v1/resource")

        assert client.rate_limit.snapshot is not None
        assert client.rate_limit.snapshot.limit == 100
        assert client.rate_limit.snapshot.remaining == 42
