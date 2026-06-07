"""019 conformance tests — generated surface end-to-end.

Covers:
  C1   — with_options() shares TokenManager; no extra token POST.
  T1   — Dinie(code=…) → 1 cc POST + 1 exchange POST; cc-bearer in exchange
          header; {code} in body; SESSION_EXCHANGE_PATH path.
  T2   — customer bearer in ALL subsequent calls (not cc-bearer).
  T3   — no code → NO /session-exchange ever (regression guard).
  T4   — token-agnostic: request is SENT with customer bearer even on
          "partner" routes; mock RECEIVES the request (no client-side gate).
  T5   — expired token → SessionTokenExpiredError (no 2nd exchange, no cc-bearer).
  T7b  — biometrics.session_exchange(code=…) round-trip: method gerado (NOT
          the TokenManager path) deserialises BiometricsSessionExchangeResponse
          carrying access_token + expires_in + customer_id.
  T8   — upload_selfie() → multipart/form-data + customer bearer in same request.
  T9   — bad code (401/403 from exchange) → typed error; _exchanged stays False;
          no caching; single-flight unlocked; no cc-bearer afterwards.
  MP   — kyc_attachments.create() is multipart/form-data (not JSON).
  E403 — 403 response maps to PermissionDeniedError (not old PermissionError).
"""

from __future__ import annotations

import json
import threading
from typing import Any

import httpx
import pytest

from dinie.generated.client import Dinie
from dinie.generated.types.biometrics_session_exchange_response import (
    BiometricsSessionExchangeResponse,
)
from dinie.runtime.errors import (
    AuthenticationError,
    PermissionDeniedError,
    SessionTokenExpiredError,
)
from dinie.runtime.token_manager import SESSION_EXCHANGE_PATH, TOKEN_PATH

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.test.dinie.com.br"
CC_TOKEN = "cc_bearer_abcdef"
CUSTOMER_TOKEN = "customer_bearer_xyz123"
CUSTOMER_ID = "cust_0987654321"
VALID_CODE = "dinie_bsc_validcode"


# ---------------------------------------------------------------------------
# Routing transport — intercepts all httpx calls at the transport level
# ---------------------------------------------------------------------------


class _Request:
    """Recorded HTTP request with parsed body."""

    def __init__(self, raw: httpx.Request) -> None:
        self.raw = raw
        self.method = raw.method
        self.url = str(raw.url)
        self.headers: dict[str, str] = dict(raw.headers)
        self._body_bytes = raw.content

    @property
    def json_body(self) -> Any:
        try:
            return json.loads(self._body_bytes)
        except Exception:
            return None

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")

    @property
    def authorization(self) -> str:
        return self.headers.get("authorization", "")

    def is_token_request(self) -> bool:
        return TOKEN_PATH in self.url

    def is_exchange_request(self) -> bool:
        return SESSION_EXCHANGE_PATH in self.url


class _RoutingTransport(httpx.BaseTransport):
    """A transport that routes requests to per-path handlers and logs them.

    Handlers are matched via substring of the URL path.  The first matching
    handler wins.  If no handler matches, returns 200 with an empty JSON object.
    """

    def __init__(self) -> None:
        self.log: list[_Request] = []
        self._routes: list[tuple[str, Any]] = []

    def route(self, path_substr: str, response: httpx.Response | None = None) -> None:
        """Register a fixed response for requests whose URL contains `path_substr`."""
        self._routes.append((path_substr, response))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        request.read()  # materialise streaming body (multipart) before logging
        logged = _Request(request)
        self.log.append(logged)
        url = str(request.url)
        for path_substr, resp in self._routes:
            if path_substr in url:
                if resp is None:
                    return httpx.Response(200, json={}, request=request)
                # Clone the response with the same request reference so httpx is happy
                return httpx.Response(
                    resp.status_code,
                    headers=dict(resp.headers),
                    content=resp.content,
                    request=request,
                )
        # Default: empty 200
        return httpx.Response(200, json={}, request=request)


# ---------------------------------------------------------------------------
# Fixtures / factories
# ---------------------------------------------------------------------------


def _cc_resp(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"access_token": CC_TOKEN, "expires_in": 3600, "token_type": "bearer"},
        request=request,
    )


def _exchange_resp(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "access_token": CUSTOMER_TOKEN,
            "expires_in": 3600,
            "token_type": "bearer",
            "customer_id": CUSTOMER_ID,
        },
        request=request,
    )


_CC_JSON = {"access_token": CC_TOKEN, "expires_in": 3600, "token_type": "bearer"}
_EX_JSON = {
    "access_token": CUSTOMER_TOKEN,
    "expires_in": 3600,
    "token_type": "bearer",
    "customer_id": CUSTOMER_ID,
}


def _make_transport() -> _RoutingTransport:
    transport = _RoutingTransport()
    transport.route(TOKEN_PATH, httpx.Response(200, json=_CC_JSON))
    transport.route(SESSION_EXCHANGE_PATH, httpx.Response(200, json=_EX_JSON))
    return transport


def _make_client(
    code: str | None = None,
    transport: _RoutingTransport | None = None,
) -> tuple[Dinie, _RoutingTransport]:
    """Return (Dinie, transport). Transport intercepts all HTTP calls."""
    t = transport or _make_transport()
    mock_http = httpx.Client(transport=t, base_url=BASE_URL)
    client = Dinie(
        client_id="test_cid",
        client_secret="test_csec",
        code=code,
        base_url=BASE_URL,
        http_client=mock_http,
    )
    return client, t


# ---------------------------------------------------------------------------
# C1 — with_options() shares TokenManager (no extra token POST)
# ---------------------------------------------------------------------------


class TestC1WithOptions:
    """DoD-C1: with_options() shares TokenManager — no extra token fetch."""

    def test_with_options_shares_token_manager(self) -> None:
        """Clone via with_options() reuses same TokenManager — no extra POST."""
        client, transport = _make_client()

        # Trigger first token fetch
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))
        _ = client.customers.list()

        before_count = sum(1 for r in transport.log if r.is_token_request())
        assert before_count == 1, "should have exactly 1 token POST before clone"

        # Clone with with_options and make a call
        clone = client.with_options(timeout=5.0)
        _ = clone.customers.list()

        after_count = sum(1 for r in transport.log if r.is_token_request())
        assert after_count == 1, (
            "with_options() clone must reuse cached token — no extra POST (C1-PY-2)"
        )

    def test_fresh_client_fetches_own_token(self) -> None:
        """A NEW Dinie instance gets its own token (control for C1)."""
        client1, transport1 = _make_client()
        client2, transport2 = _make_client()

        transport1.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))
        transport2.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client1.customers.list()
        client2.customers.list()

        assert sum(1 for r in transport1.log if r.is_token_request()) == 1
        assert sum(1 for r in transport2.log if r.is_token_request()) == 1

    def test_with_options_shared_customer_token(self) -> None:
        """Session-mode clone also shares customer token (no 2nd exchange)."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()  # triggers cc + exchange

        before_token = sum(1 for r in transport.log if r.is_token_request())
        before_exchange = sum(1 for r in transport.log if r.is_exchange_request())
        assert before_token == 1
        assert before_exchange == 1

        clone = client.with_options(timeout=10.0)
        clone.customers.list()  # should use cached customer token

        assert sum(1 for r in transport.log if r.is_token_request()) == 1, "no extra cc POST"
        assert sum(1 for r in transport.log if r.is_exchange_request()) == 1, "no extra exchange"


# ---------------------------------------------------------------------------
# T1 — two-step count, cc-bearer in exchange header, {code} in body
# ---------------------------------------------------------------------------


class TestT1TwoStep:
    """DoD-T1: exactly 1 cc POST + 1 exchange POST; cc-bearer in exchange header."""

    def test_two_step_counts(self) -> None:
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        cc_reqs = [r for r in transport.log if r.is_token_request()]
        ex_reqs = [r for r in transport.log if r.is_exchange_request()]
        assert len(cc_reqs) == 1, "exactly 1 POST /auth/token"
        assert len(ex_reqs) == 1, "exactly 1 POST /biometrics/session-exchange"

    def test_exchange_header_carries_cc_bearer(self) -> None:
        """Exchange request must carry the cc-bearer from step 1."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        ex_req = next(r for r in transport.log if r.is_exchange_request())
        assert ex_req.authorization == f"Bearer {CC_TOKEN}", (
            "exchange must carry cc-bearer in Authorization header"
        )

    def test_exchange_body_carries_code(self) -> None:
        """Exchange body must contain {code}."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        ex_req = next(r for r in transport.log if r.is_exchange_request())
        assert ex_req.json_body == {"code": VALID_CODE}

    def test_exchange_hits_correct_path(self) -> None:
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        ex_req = next(r for r in transport.log if r.is_exchange_request())
        assert SESSION_EXCHANGE_PATH in ex_req.url

    def test_single_flight_n_concurrent(self) -> None:
        """N concurrent first-calls → still exactly 1 cc POST + 1 exchange POST."""
        N = 10
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        gate: list[bool] = []
        errors: list[BaseException] = []
        start = threading.Barrier(N)

        def _call() -> None:
            try:
                start.wait()
                client.customers.list()
                gate.append(True)
            except BaseException as e:
                errors.append(e)

        threads = [threading.Thread(target=_call) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"threads raised: {errors}"
        assert len(gate) == N

        cc_count = sum(1 for r in transport.log if r.is_token_request())
        ex_count = sum(1 for r in transport.log if r.is_exchange_request())
        assert cc_count == 1, f"expected 1 cc POST, got {cc_count}"
        assert ex_count == 1, f"expected 1 exchange POST, got {ex_count}"


# ---------------------------------------------------------------------------
# T2 — customer bearer in all subsequent calls
# ---------------------------------------------------------------------------


class TestT2CustomerBearer:
    """DoD-T2: all API calls carry customer bearer after exchange."""

    def test_api_calls_carry_customer_bearer(self) -> None:
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()
        client.customers.list()  # 2nd call — cached token

        api_reqs = [
            r for r in transport.log if not r.is_token_request() and not r.is_exchange_request()
        ]
        assert len(api_reqs) >= 2
        for req in api_reqs:
            assert req.authorization == f"Bearer {CUSTOMER_TOKEN}", (
                f"expected customer bearer, got {req.authorization!r}"
            )

    def test_cc_bearer_never_used_in_api_calls(self) -> None:
        """The cc-bearer must NOT appear in any API call Authorization header."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        api_reqs = [
            r for r in transport.log if not r.is_token_request() and not r.is_exchange_request()
        ]
        for req in api_reqs:
            assert req.authorization != f"Bearer {CC_TOKEN}", (
                "cc-bearer must NOT appear in API calls"
            )


# ---------------------------------------------------------------------------
# T3 — partner mode (no code) unchanged
# ---------------------------------------------------------------------------


class TestT3PartnerModeRegression:
    """DoD-T3: without code, no /session-exchange ever."""

    def test_partner_mode_no_exchange(self) -> None:
        client, transport = _make_client(code=None)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()
        client.customers.list()

        ex_reqs = [r for r in transport.log if r.is_exchange_request()]
        assert len(ex_reqs) == 0, "partner mode must never hit /session-exchange"

    def test_partner_mode_uses_cc_bearer(self) -> None:
        client, transport = _make_client(code=None)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()

        api_reqs = [r for r in transport.log if not r.is_token_request()]
        assert all(r.authorization == f"Bearer {CC_TOKEN}" for r in api_reqs)


# ---------------------------------------------------------------------------
# T4 — token-agnostic routing (request SENT with customer bearer)
# ---------------------------------------------------------------------------


class TestT4TokenAgnostic:
    """DoD-T4: request is sent to the wire with customer bearer; no client-side gate."""

    def test_request_arrives_at_wire_with_customer_bearer(self) -> None:
        """Mock receives the request — proves no client-side gate blocked it."""
        client, transport = _make_client(code=VALID_CODE)
        # Simulate a "partner route" returning 403
        _forbidden = {"type": "https://docs.dinie.com/errors/forbidden", "detail": "Forbidden"}
        transport.route("/customers", httpx.Response(403, json=_forbidden))

        with pytest.raises(PermissionDeniedError):
            client.customers.list()

        # The mock RECEIVED the request (gate would have prevented this)
        customer_reqs = [
            r
            for r in transport.log
            if "/customers" in r.url and not r.is_token_request() and not r.is_exchange_request()
        ]
        assert len(customer_reqs) >= 1, "request must have reached the mock (no client-side gate)"
        assert customer_reqs[0].authorization == f"Bearer {CUSTOMER_TOKEN}", (
            "the request on the wire must carry the customer bearer, not cc-bearer"
        )


# ---------------------------------------------------------------------------
# T5 — expiry raises SessionTokenExpiredError
# ---------------------------------------------------------------------------


class TestT5Expiry:
    """DoD-T5: expired token → SessionTokenExpiredError; no 2nd exchange; no cc-bearer."""

    def test_invalidate_raises_session_token_expired(self) -> None:
        """After invalidate(), next call raises SessionTokenExpiredError (no retry)."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        # Trigger successful exchange
        client.customers.list()

        # Invalidate simulates 401 / TTL expiry
        client._token_manager.invalidate()

        before_count = len(transport.log)

        with pytest.raises(SessionTokenExpiredError):
            client.customers.list()

        # No new exchange must have occurred
        new_exchange = [r for r in transport.log[before_count:] if r.is_exchange_request()]
        assert len(new_exchange) == 0, "no 2nd exchange after expiry"

    def test_no_cc_bearer_after_expiry(self) -> None:
        """SessionTokenExpiredError is raised before any network call (no cc-bearer in wire)."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        client.customers.list()
        client._token_manager.invalidate()
        before_count = len(transport.log)

        with pytest.raises(SessionTokenExpiredError):
            client.customers.list()

        # No new token POSTs after invalidation
        new_cc = [r for r in transport.log[before_count:] if r.is_token_request()]
        assert len(new_cc) == 0, "no cc-bearer request after expiry — SDK raises before network"


# ---------------------------------------------------------------------------
# T7(b) — biometrics.session_exchange() round-trip (generated method, not manager)
# ---------------------------------------------------------------------------


class TestT7bSessionExchangeRoundTrip:
    """DoD-T7(b): generated method biometrics.session_exchange() round-trip.

    Code path: surface method → SyncHttpClient.request() → response deserialise.
    This is DISTINCT from the TokenManager path (T1/T5 exercise the manager).
    """

    def test_session_exchange_returns_typed_response(self) -> None:
        """session_exchange() returns BiometricsSessionExchangeResponse (typed, not dict)."""
        client, _ = _make_client(code=None)  # partner mode — session_exchange is explicit
        result = client.biometrics.session_exchange({"code": VALID_CODE})

        assert isinstance(result, BiometricsSessionExchangeResponse), (
            f"expected BiometricsSessionExchangeResponse, got {type(result)}"
        )

    def test_session_exchange_carries_customer_id(self) -> None:
        """Deserialised response includes customer_id (X1 anti-drop check)."""
        client, _ = _make_client(code=None)
        result = client.biometrics.session_exchange({"code": VALID_CODE})

        assert result.customer_id == CUSTOMER_ID, "customer_id must survive deserialisation"

    def test_session_exchange_carries_access_token_and_expires_in(self) -> None:
        client, _ = _make_client(code=None)
        result = client.biometrics.session_exchange({"code": VALID_CODE})

        assert result.access_token == CUSTOMER_TOKEN
        assert result.expires_in == 3600
        assert result.token_type == "bearer"

    def test_session_exchange_sends_code_body(self) -> None:
        """Generated method serialises {code} to the wire (not something else)."""
        client, transport = _make_client(code=None)
        client.biometrics.session_exchange({"code": VALID_CODE})

        ex_reqs = [r for r in transport.log if r.is_exchange_request()]
        assert len(ex_reqs) == 1
        body = ex_reqs[0].json_body
        assert isinstance(body, dict) and body.get("code") == VALID_CODE

    def test_session_exchange_is_distinct_from_token_manager_path(self) -> None:
        """surface method does NOT affect the TokenManager state."""
        client, transport = _make_client(code=None)
        # Call the method
        client.biometrics.session_exchange({"code": VALID_CODE})

        # The TokenManager should still be in partner mode (no exchange via manager)
        # i.e., it fetches cc-bearer on next token request
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))
        client.customers.list()

        cc_reqs = [r for r in transport.log if r.is_token_request()]
        ex_via_method = [r for r in transport.log if r.is_exchange_request()]

        # session_exchange (surface) fires 1 exchange, customer.list fires 1 cc token
        assert len(cc_reqs) == 1  # 1 from customers.list() (partner mode)
        assert len(ex_via_method) == 1  # 1 from biometrics.session_exchange() (surface)


# ---------------------------------------------------------------------------
# T8 — upload_selfie: multipart + customer bearer in the same request
# ---------------------------------------------------------------------------


class TestT8SelfieMultipartBearer:
    """DoD-T8: selfie upload is multipart/form-data AND carries customer bearer."""

    def test_upload_selfie_is_multipart(self) -> None:
        client, transport = _make_client(code=VALID_CODE)
        transport.route(
            "/kyc-attachments/selfie",
            httpx.Response(201, json={"attachment_type": "selfie", "submitted": True}),
        )

        # MultipartBody.file expects bytes (or IO); filename/content-type are separate fields.
        client.customers.kyc_attachments.upload_selfie(
            customer_id="cust_abc",
            params={"requirement_id": "req_selfie_001", "file": b"fake jpeg content"},
        )

        selfie_reqs = [r for r in transport.log if "/kyc-attachments/selfie" in r.url]
        assert len(selfie_reqs) == 1
        ct = selfie_reqs[0].content_type
        assert "multipart/form-data" in ct, f"expected multipart, got {ct!r}"

    def test_upload_selfie_carries_customer_bearer(self) -> None:
        client, transport = _make_client(code=VALID_CODE)
        transport.route(
            "/kyc-attachments/selfie",
            httpx.Response(201, json={"attachment_type": "selfie", "submitted": True}),
        )

        client.customers.kyc_attachments.upload_selfie(
            customer_id="cust_abc",
            params={"requirement_id": "req_selfie_001", "file": b"fake jpeg content"},
        )

        selfie_reqs = [r for r in transport.log if "/kyc-attachments/selfie" in r.url]
        assert selfie_reqs[0].authorization == f"Bearer {CUSTOMER_TOKEN}", (
            "selfie upload must carry customer bearer (token-agnostic)"
        )

    def test_upload_selfie_not_json(self) -> None:
        """upload_selfie must NOT send application/json."""
        client, transport = _make_client(code=VALID_CODE)
        transport.route(
            "/kyc-attachments/selfie",
            httpx.Response(201, json={"attachment_type": "selfie", "submitted": True}),
        )

        client.customers.kyc_attachments.upload_selfie(
            customer_id="cust_abc",
            params={"requirement_id": "req_selfie_001", "file": b"data"},
        )

        selfie_reqs = [r for r in transport.log if "/kyc-attachments/selfie" in r.url]
        ct = selfie_reqs[0].content_type
        assert "application/json" not in ct, "selfie must not be JSON"


# ---------------------------------------------------------------------------
# MP — kyc_attachments.create() is also multipart (not JSON)
# ---------------------------------------------------------------------------


class TestMultipartKycCreate:
    """kyc_attachments.create() sends multipart/form-data (not JSON)."""

    def test_kyc_create_is_multipart(self) -> None:
        client, transport = _make_client()
        transport.route(
            "/kyc-attachments",
            httpx.Response(201, json={"attachment_type": "document", "submitted": False}),
        )

        client.customers.kyc_attachments.create(
            customer_id="cust_abc",
            params={"requirement_id": "req_001", "file": b"pdf content"},
        )

        kyc_reqs = [
            r
            for r in transport.log
            if "/kyc-attachments" in r.url
            and "/selfie" not in r.url
            and not r.is_token_request()
            and not r.is_exchange_request()
        ]
        assert len(kyc_reqs) == 1
        ct = kyc_reqs[0].content_type
        assert "multipart/form-data" in ct, f"kyc create must be multipart, got {ct!r}"
        assert "application/json" not in ct


# ---------------------------------------------------------------------------
# T9 — bad code → typed error; no cache; no retry; single-flight unlocked
# ---------------------------------------------------------------------------


class TestT9BadCode:
    """DoD-T9: exchange 401/403 → typed error; _exchanged stays False; single-flight unlocked."""

    _AUTH_ERR = {"type": "https://docs.dinie.com/errors/authentication-failed", "detail": "bad"}
    _FORBID_ERR = {"type": "https://docs.dinie.com/errors/forbidden", "detail": "bad"}

    def _make_failing_transport(self, status: int) -> _RoutingTransport:
        t = _RoutingTransport()
        t.route(TOKEN_PATH, httpx.Response(200, json=_CC_JSON))
        t.route(SESSION_EXCHANGE_PATH, httpx.Response(status, json=self._AUTH_ERR))
        return t

    def test_401_from_exchange_raises_auth_error(self) -> None:
        transport = self._make_failing_transport(401)
        client, _ = _make_client(code="bad_code", transport=transport)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        with pytest.raises(AuthenticationError):
            client.customers.list()

    def test_403_from_exchange_raises_permission_denied(self) -> None:
        transport = self._make_failing_transport(403)
        # Override exchange to return 403
        transport._routes = [
            (TOKEN_PATH, httpx.Response(200, json=_CC_JSON)),
            (SESSION_EXCHANGE_PATH, httpx.Response(403, json=self._FORBID_ERR)),
        ]
        client, _ = _make_client(code="bad_code", transport=transport)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        with pytest.raises(PermissionDeniedError):
            client.customers.list()

    def test_no_customer_token_cached_after_failure(self) -> None:
        """After exchange fails, token must NOT be cached; next call re-attempts exchange."""
        transport = self._make_failing_transport(401)
        client, _ = _make_client(code="bad_code", transport=transport)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        with pytest.raises(AuthenticationError):
            client.customers.list()

        ex_count_after_1 = sum(1 for r in transport.log if r.is_exchange_request())
        assert ex_count_after_1 == 1

        with pytest.raises(AuthenticationError):
            client.customers.list()

        # Second call also triggers a new cc + exchange (not_exchanged → re-tries)
        ex_count_after_2 = sum(1 for r in transport.log if r.is_exchange_request())
        assert ex_count_after_2 == 2, "failed exchange must not be cached; next call retries"

    def test_single_flight_unlocks_on_failure(self) -> None:
        """N concurrent callers all get the typed error; no deadlock."""
        N = 5
        transport = self._make_failing_transport(401)
        client, _ = _make_client(code="bad_code", transport=transport)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        errors: list[BaseException] = []
        start = threading.Barrier(N)

        def _call() -> None:
            try:
                start.wait()
                client.customers.list()
            except BaseException as e:
                errors.append(e)

        threads = [threading.Thread(target=_call) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == N, f"all {N} threads must raise; got {len(errors)}"
        for e in errors:
            assert isinstance(e, AuthenticationError), (
                f"expected AuthenticationError, got {type(e)}"
            )

    def test_not_session_token_expired_error(self) -> None:
        """T9 raises AuthenticationError, NOT SessionTokenExpiredError (distinct from T5)."""
        transport = self._make_failing_transport(401)
        client, _ = _make_client(code="bad_code", transport=transport)
        transport.route("/customers", httpx.Response(200, json={"data": [], "next_cursor": None}))

        with pytest.raises(AuthenticationError):
            client.customers.list()

        # Must NOT be SessionTokenExpiredError (T5 is for obtained-and-expired token)
        try:
            client.customers.list()
        except SessionTokenExpiredError:
            pytest.fail("T9 must not raise SessionTokenExpiredError (that is T5)")
        except AuthenticationError:
            pass  # expected


# ---------------------------------------------------------------------------
# E403 — 403 maps to PermissionDeniedError (not old PermissionError)
# ---------------------------------------------------------------------------


class TestE403PermissionDeniedError:
    """403 responses map to PermissionDeniedError (new name, post-014 rename)."""

    def test_403_api_response_raises_permission_denied_error(self) -> None:
        client, transport = _make_client()
        _forbidden = {"type": "https://docs.dinie.com/errors/forbidden", "detail": "Forbidden"}
        transport.route("/customers", httpx.Response(403, json=_forbidden))

        with pytest.raises(PermissionDeniedError):
            client.customers.list()

    def test_403_class_name_is_permission_denied_error(self) -> None:
        """Verify the class name — guards against old PermissionError name."""
        assert PermissionDeniedError.__name__ == "PermissionDeniedError"

    def test_no_permission_error_in_generated_errors(self) -> None:
        """Old PermissionError must not exist in generated errors namespace."""
        import dinie.generated.errors as errs

        assert not hasattr(errs, "PermissionError"), (
            "generated.errors must not export old PermissionError class"
        )
        assert hasattr(errs, "PermissionDeniedError"), (
            "generated.errors must export PermissionDeniedError"
        )


# ---------------------------------------------------------------------------
# Lazy constructor — no I/O on Dinie() init
# ---------------------------------------------------------------------------


class TestLazyConstructor:
    """Dinie() and Dinie(code=…) must not do I/O in __init__."""

    def test_partner_constructor_is_lazy(self) -> None:
        # Use a transport that would fail loudly if called
        transport = _RoutingTransport()
        mock_http = httpx.Client(transport=transport, base_url=BASE_URL)
        Dinie(client_id="cid", client_secret="csec", base_url=BASE_URL, http_client=mock_http)
        assert len(transport.log) == 0, "partner constructor must not make any HTTP call"

    def test_session_constructor_is_lazy(self) -> None:
        transport = _RoutingTransport()
        mock_http = httpx.Client(transport=transport, base_url=BASE_URL)
        Dinie(
            client_id="cid",
            client_secret="csec",
            code=VALID_CODE,
            base_url=BASE_URL,
            http_client=mock_http,
        )
        assert len(transport.log) == 0, "session constructor (code=…) must not make any HTTP call"
