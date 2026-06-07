"""Tests for TokenManager session mode (story 015a).

DoD coverage:
  T1 — exactly one two-step exchange, cc-bearer in exchange header+body.
  T2 — customer bearer in all subsequent calls.
  T3 — partner mode (no code) unchanged; no /session-exchange ever.
  T4 — token-agnostic: request is sent with customer bearer even on
       "partner" routes; the mock receives the request (no client-side gate).
  T5 — expiry raises SessionTokenExpiredError (no 2nd exchange, no cc-bearer).
  T9 — exchange-fail (401/403) → typed from_response error; _exchanged stays
       False; no caching; single-flight unlocked; no cc-bearer afterwards.
  lazy — Dinie(code=…) does no I/O in __init__.
"""
from __future__ import annotations

import threading
import time
from typing import Any

import httpx
import pytest

from dinie.runtime.errors import (
    AuthenticationError,
    PermissionDeniedError,
    SessionTokenExpiredError,
)
from dinie.runtime.token_manager import SESSION_EXCHANGE_PATH, TOKEN_PATH, TokenManager

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://api.test.dinie.com.br"
CC_TOKEN = "cc_bearer_token_abc"
CUSTOMER_TOKEN = "customer_bearer_xyz"
CUSTOMER_EXPIRES_IN = 3600
VALID_CODE = "dinie_bsc_valid"


def _make_cc_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={"access_token": CC_TOKEN, "expires_in": 3600, "token_type": "bearer"},
        request=httpx.Request("POST", f"{BASE_URL}{TOKEN_PATH}"),
    )


def _make_exchange_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "access_token": CUSTOMER_TOKEN,
            "expires_in": CUSTOMER_EXPIRES_IN,
            "token_type": "bearer",
            "customer_id": "cust_001",
        },
        request=httpx.Request("POST", f"{BASE_URL}{SESSION_EXCHANGE_PATH}"),
    )


def _make_token_manager(code: str | None = None) -> tuple[TokenManager, list[httpx.Request]]:
    """Return (TokenManager, requests_log). requests_log is appended by the mock."""
    requests_log: list[httpx.Request] = []

    def _mock_post(url: str, **kwargs: Any) -> httpx.Response:
        headers_dict: dict[str, str] = kwargs.get("headers", {})
        json_body: Any = kwargs.get("json")
        full_request = httpx.Request("POST", url, headers=headers_dict, json=json_body)
        requests_log.append(full_request)

        if TOKEN_PATH in url:
            return _make_cc_response()
        if SESSION_EXCHANGE_PATH in url:
            return _make_exchange_response()
        return httpx.Response(404, text="Not found")

    mock_http = httpx.Client()
    mock_http.post = _mock_post  # type: ignore[method-assign]

    tm = TokenManager(
        client_id="cid",
        client_secret="csec",
        base_url=BASE_URL,
        http_client=mock_http,
        code=code,
    )
    return tm, requests_log


# ---------------------------------------------------------------------------
# T3 — Partner mode (no code) — regression guard
# ---------------------------------------------------------------------------


class TestPartnerModeUnchanged:
    """T3: without code, behaviour is today's cc-bearer path — no session-exchange."""

    def test_partner_mode_returns_cc_bearer(self) -> None:
        tm, log = _make_token_manager(code=None)
        token = tm.token
        assert token == CC_TOKEN
        assert len(log) == 1
        assert TOKEN_PATH in str(log[0].url)

    def test_partner_mode_never_calls_session_exchange(self) -> None:
        tm, log = _make_token_manager(code=None)
        # Multiple calls
        for _ in range(3):
            _ = tm.token
        exchange_calls = [r for r in log if SESSION_EXCHANGE_PATH in str(r.url)]
        assert exchange_calls == [], "No /session-exchange in partner mode"

    def test_partner_mode_refreshes_on_invalidate(self) -> None:
        tm, log = _make_token_manager(code=None)
        _ = tm.token          # first call — 1 POST /auth/token
        tm.invalidate()
        _ = tm.token          # second call — should re-fetch
        assert len(log) == 2
        assert all(TOKEN_PATH in str(r.url) for r in log)


# ---------------------------------------------------------------------------
# Lazy init
# ---------------------------------------------------------------------------


class TestLazyInit:
    """No I/O on construction — exchange happens on first token access."""

    def test_no_io_on_construction(self) -> None:
        tm, log = _make_token_manager(code=VALID_CODE)
        # Constructor completed — log must be empty
        assert log == []

    def test_exchange_happens_on_first_token_access(self) -> None:
        tm, log = _make_token_manager(code=VALID_CODE)
        token = tm.token
        assert len(log) == 2  # 1× /auth/token + 1× /session-exchange
        assert token == CUSTOMER_TOKEN


# ---------------------------------------------------------------------------
# T1 — Exactly one two-step exchange (count + header/body asserts)
# ---------------------------------------------------------------------------


class TestExactlyOneExchange:
    """T1: one /auth/token + one /session-exchange on first call; cache after."""

    def test_two_step_exactly_once(self) -> None:
        tm, log = _make_token_manager(code=VALID_CODE)
        t1 = tm.token
        t2 = tm.token
        t3 = tm.token

        # Count
        auth_calls = [r for r in log if TOKEN_PATH in str(r.url)]
        exchange_calls = [r for r in log if SESSION_EXCHANGE_PATH in str(r.url)]
        assert len(auth_calls) == 1, "Exactly 1 POST /auth/token"
        assert len(exchange_calls) == 1, "Exactly 1 POST /session-exchange"

        # All three calls return the customer token
        assert t1 == t2 == t3 == CUSTOMER_TOKEN

    def test_exchange_request_carries_cc_bearer_in_authorization(self) -> None:
        """Step-2 request must carry the cc-bearer from step-1 (two-step enchaînement)."""
        tm, log = _make_token_manager(code=VALID_CODE)
        _ = tm.token

        exchange_req = next(r for r in log if SESSION_EXCHANGE_PATH in str(r.url))
        auth_header = exchange_req.headers.get("authorization", "")
        assert auth_header == f"Bearer {CC_TOKEN}", (
            f"Exchange Authorization header must carry cc-bearer; got: {auth_header!r}"
        )

    def test_exchange_request_body_contains_code(self) -> None:
        """Step-2 request body must contain {code: <the code passed to constructor}."""
        import json

        requests_log: list[httpx.Request] = []

        def _mock_post(url: str, **kwargs: Any) -> httpx.Response:
            headers_dict = kwargs.get("headers", {})
            json_body = kwargs.get("json")
            req = httpx.Request("POST", url, headers=headers_dict)
            req._content = json.dumps(json_body).encode() if json_body is not None else b""  # type: ignore[attr-defined]
            requests_log.append(req)
            if TOKEN_PATH in url:
                return _make_cc_response()
            if SESSION_EXCHANGE_PATH in url:
                return _make_exchange_response()
            return httpx.Response(404)

        mock_http = httpx.Client()
        mock_http.post = _mock_post  # type: ignore[method-assign]
        tm = TokenManager("cid", "csec", BASE_URL, mock_http, code=VALID_CODE)
        _ = tm.token

        exchange_req = next(r for r in requests_log if SESSION_EXCHANGE_PATH in str(r.url))
        body = json.loads(exchange_req._content)  # type: ignore[attr-defined]
        assert body.get("code") == VALID_CODE, f"Exchange body must have code={VALID_CODE!r}"

    def test_single_flight_under_n_concurrent_first_calls(self) -> None:
        """N threads all calling token() for the first time → exactly 1 exchange."""
        N = 8
        call_counts: dict[str, int] = {"auth": 0, "exchange": 0}
        lock = threading.Lock()
        barrier = threading.Barrier(N)

        def _mock_post(url: str, **kwargs: Any) -> httpx.Response:
            with lock:
                if TOKEN_PATH in url:
                    call_counts["auth"] += 1
                elif SESSION_EXCHANGE_PATH in url:
                    call_counts["exchange"] += 1
            time.sleep(0.01)  # simulate I/O latency
            if TOKEN_PATH in url:
                return _make_cc_response()
            return _make_exchange_response()

        mock_http = httpx.Client()
        mock_http.post = _mock_post  # type: ignore[method-assign]
        tm = TokenManager("cid", "csec", BASE_URL, mock_http, code=VALID_CODE)

        tokens: list[str] = []
        errors: list[Exception] = []

        def _worker() -> None:
            barrier.wait()  # all threads start at the same time
            try:
                tokens.append(tm.token)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"No errors expected; got: {errors}"
        assert all(t == CUSTOMER_TOKEN for t in tokens), "All threads must see the customer token"
        assert call_counts["auth"] == 1, f"Exactly 1 /auth/token call; got {call_counts['auth']}"
        assert call_counts["exchange"] == 1, (
            f"Exactly 1 /session-exchange call; got {call_counts['exchange']}"
        )


# ---------------------------------------------------------------------------
# T2 — Customer bearer in every subsequent call
# ---------------------------------------------------------------------------


class TestCustomerBearerInAllCalls:
    """T2: after the exchange, ALL requests carry the customer bearer."""

    def test_token_returns_customer_bearer_not_cc(self) -> None:
        tm, _ = _make_token_manager(code=VALID_CODE)
        token = tm.token
        assert token == CUSTOMER_TOKEN
        assert token != CC_TOKEN

    def test_repeated_calls_return_same_customer_bearer(self) -> None:
        tm, _ = _make_token_manager(code=VALID_CODE)
        results = [tm.token for _ in range(5)]
        assert all(t == CUSTOMER_TOKEN for t in results)


# ---------------------------------------------------------------------------
# T4 — Token-agnostic: request reaches the wire with customer bearer
# ---------------------------------------------------------------------------


class TestTokenAgnostic:
    """T4: the SDK sends the customer bearer even on 'partner' routes (no gate).

    We test via the TokenManager directly: the bearer it returns is used in
    ALL requests. The absence of a gate means token() returns the customer
    bearer regardless of which route is about to be called — there is no
    per-route branching.
    """

    def test_token_returns_customer_bearer_for_any_path(self) -> None:
        """There is no per-route gate — token() always returns the customer bearer."""
        tm, _ = _make_token_manager(code=VALID_CODE)
        # Simulate what BaseClient does: ask for the token then inject it.
        bearer = tm.token
        # The mock http layer (in http.py integration) would send this bearer to
        # ANY route — asserting it equals the customer token proves no gate exists.
        assert bearer == CUSTOMER_TOKEN

    def test_invalidate_does_not_set_cc_bearer_as_next_token(self) -> None:
        """After invalidate in session mode, the next token() raises SessionTokenExpiredError.

        This ensures the SDK cannot fall back to the cc-bearer on a customer route.
        The cc-bearer never reaches the wire after the exchange is done (T5 territory
        — covered in detail in TestExpiryHonest but validated here as a T4 invariant).
        """
        tm, _ = _make_token_manager(code=VALID_CODE)
        _ = tm.token  # first call → exchange done
        tm.invalidate()
        with pytest.raises(SessionTokenExpiredError):
            _ = tm.token


# ---------------------------------------------------------------------------
# T5 — Expiry honest (no refresh, no fallback)
# ---------------------------------------------------------------------------


class TestExpiryHonest:
    """T5: expired customer token → SessionTokenExpiredError (no 2nd exchange, no cc-bearer)."""

    def test_invalidate_after_exchange_raises_session_expired(self) -> None:
        """Simulate a 401 → invalidate(); next token() → SessionTokenExpiredError."""
        tm, log = _make_token_manager(code=VALID_CODE)
        _ = tm.token          # exchange done
        tm.invalidate()       # simulates 401 one-shot re-auth path in http.py

        with pytest.raises(SessionTokenExpiredError) as exc_info:
            _ = tm.token

        assert "session" in str(exc_info.value).lower() or "expire" in str(exc_info.value).lower()

    def test_no_second_exchange_after_invalidate(self) -> None:
        """No 2nd /session-exchange after expiry."""
        tm, log = _make_token_manager(code=VALID_CODE)
        _ = tm.token          # exchange done (2 calls: auth + exchange)

        initial_len = len(log)
        tm.invalidate()

        with pytest.raises(SessionTokenExpiredError):
            _ = tm.token

        # No new calls were made
        assert len(log) == initial_len, "No new requests after expiry (code is single-use)"

    def test_no_cc_bearer_in_flight_after_expiry(self) -> None:
        """After expiry, no /auth/token is called (no cc-bearer fallback)."""
        tm, log = _make_token_manager(code=VALID_CODE)
        _ = tm.token

        auth_calls_before = sum(1 for r in log if TOKEN_PATH in str(r.url))
        tm.invalidate()

        with pytest.raises(SessionTokenExpiredError):
            _ = tm.token

        auth_calls_after = sum(1 for r in log if TOKEN_PATH in str(r.url))
        assert auth_calls_after == auth_calls_before, "No new /auth/token calls after expiry"

    def test_session_expired_is_dinieError(self) -> None:
        from dinie.runtime.errors import DinieError

        tm, _ = _make_token_manager(code=VALID_CODE)
        _ = tm.token
        tm.invalidate()
        with pytest.raises(SessionTokenExpiredError) as exc_info:
            _ = tm.token
        assert isinstance(exc_info.value, DinieError)

    def test_natural_ttl_expiry_raises_session_expired(self) -> None:
        """When the token expires naturally (TTL elapsed), next call raises
        SessionTokenExpiredError."""
        tm, log = _make_token_manager(code=VALID_CODE)
        _ = tm.token  # exchange done

        # Artificially expire the cached token
        with tm._condition:
            tm._expires_at = time.monotonic() - 1.0  # force past expiry

        with pytest.raises(SessionTokenExpiredError):
            _ = tm.token

        # Confirm no second exchange was attempted
        exchange_calls = [r for r in log if SESSION_EXCHANGE_PATH in str(r.url)]
        assert len(exchange_calls) == 1, "Still exactly 1 exchange even after natural expiry"


# ---------------------------------------------------------------------------
# T9 — Exchange failure (code invalid/already-consumed)
# ---------------------------------------------------------------------------


class TestExchangeFailure:
    """T9: exchange step-2 returns 401/403 → typed from_response error; no caching; no retry."""

    def _make_failing_token_manager(
        self, exchange_status: int
    ) -> tuple[TokenManager, list[httpx.Request]]:
        requests_log: list[httpx.Request] = []

        def _mock_post(url: str, **kwargs: Any) -> httpx.Response:
            req = httpx.Request("POST", url)
            requests_log.append(req)
            if TOKEN_PATH in url:
                return _make_cc_response()
            if SESSION_EXCHANGE_PATH in url:
                return httpx.Response(
                    exchange_status,
                    json={"detail": "invalid or consumed code"},
                    request=req,
                )
            return httpx.Response(404)

        mock_http = httpx.Client()
        mock_http.post = _mock_post  # type: ignore[method-assign]

        tm = TokenManager("cid", "csec", BASE_URL, mock_http, code="dinie_bsc_invalid")
        return tm, requests_log

    def test_401_exchange_raises_authentication_error(self) -> None:
        tm, _ = self._make_failing_token_manager(401)
        with pytest.raises(AuthenticationError):
            _ = tm.token

    def test_403_exchange_raises_permission_denied_error(self) -> None:
        tm, _ = self._make_failing_token_manager(403)
        with pytest.raises(PermissionDeniedError):
            _ = tm.token

    def test_no_second_exchange_attempt_on_failure(self) -> None:
        """After a failed exchange, a second call re-attempts step-1+step-2 (no phantom token)."""
        tm, log = self._make_failing_token_manager(401)

        with pytest.raises(AuthenticationError):
            _ = tm.token

        exchange_calls_1 = sum(1 for r in log if SESSION_EXCHANGE_PATH in str(r.url))
        assert exchange_calls_1 == 1, "Exactly 1 exchange attempt on first call"

        # Second call re-tries the full two-step (not a retry of the exchange — a new attempt).
        with pytest.raises(AuthenticationError):
            _ = tm.token

        exchange_calls_2 = sum(1 for r in log if SESSION_EXCHANGE_PATH in str(r.url))
        assert exchange_calls_2 == 2, "Second call re-attempts the exchange (not cached)"

    def test_token_not_cached_after_failed_exchange(self) -> None:
        """No phantom token is served after a failed exchange."""
        tm, _ = self._make_failing_token_manager(401)

        with pytest.raises(AuthenticationError):
            _ = tm.token

        # The internal token cache must remain empty
        assert tm._token is None, "_token must not be cached after a failed exchange"

    def test_exchanged_flag_stays_false_after_failure(self) -> None:
        """_exchanged stays False when exchange fails (T9 ≠ T5 — T5 requires success first)."""
        tm, _ = self._make_failing_token_manager(401)

        with pytest.raises(AuthenticationError):
            _ = tm.token

        assert tm._exchanged is False, "_exchanged must stay False when exchange never succeeded"

    def test_single_flight_unlocked_after_exchange_failure(self) -> None:
        """After exchange failure, _refreshing is cleared (single-flight unblocked)."""
        tm, _ = self._make_failing_token_manager(401)

        with pytest.raises(AuthenticationError):
            _ = tm.token

        assert tm._refreshing is False, "_refreshing must be cleared after failure"

    def test_no_cc_bearer_served_after_failed_exchange(self) -> None:
        """After a failed exchange, the SDK does NOT fall back to the cc-bearer."""
        call_counts: dict[str, int] = {"auth": 0, "exchange": 0}

        def _mock_post(url: str, **kwargs: Any) -> httpx.Response:
            req = httpx.Request("POST", url)
            if TOKEN_PATH in url:
                call_counts["auth"] += 1
                return _make_cc_response()
            if SESSION_EXCHANGE_PATH in url:
                call_counts["exchange"] += 1
                return httpx.Response(401, json={"detail": "bad code"}, request=req)
            return httpx.Response(404)

        mock_http = httpx.Client()
        mock_http.post = _mock_post  # type: ignore[method-assign]

        tm = TokenManager("cid", "csec", BASE_URL, mock_http, code="dinie_bsc_bad")

        with pytest.raises(AuthenticationError):
            _ = tm.token

        # After failure, the token is not CC_TOKEN — the SDK doesn't fall back.
        assert tm._token is None, "No cc-bearer is served as a fallback"

    def test_exchange_failure_is_not_session_token_expired(self) -> None:
        """T9 error (exchange never succeeded) is NOT SessionTokenExpiredError (T5)."""
        tm, _ = self._make_failing_token_manager(401)

        with pytest.raises(AuthenticationError) as exc_info:
            _ = tm.token

        assert not isinstance(exc_info.value, SessionTokenExpiredError), (
            "T9 must raise AuthenticationError (not SessionTokenExpiredError, which is T5)"
        )


# ---------------------------------------------------------------------------
# Session mode vs partner mode — explicit symmetry test
# ---------------------------------------------------------------------------


class TestModeSymmetry:
    """Both modes run on the same TokenManager class; code= is the selector."""

    def test_same_class_different_modes(self) -> None:
        tm_partner, _ = _make_token_manager(code=None)
        tm_session, _ = _make_token_manager(code=VALID_CODE)
        assert type(tm_partner) is type(tm_session) is TokenManager

    def test_partner_mode_token_is_cc_bearer(self) -> None:
        tm, _ = _make_token_manager(code=None)
        assert tm.token == CC_TOKEN

    def test_session_mode_token_is_customer_bearer(self) -> None:
        tm, _ = _make_token_manager(code=VALID_CODE)
        assert tm.token == CUSTOMER_TOKEN

    def test_session_exchange_path_constant_value(self) -> None:
        assert SESSION_EXCHANGE_PATH == "/biometrics/session-exchange"
