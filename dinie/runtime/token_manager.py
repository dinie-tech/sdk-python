"""Token-lifecycle manager for the Dinie Python SDK.

Responsibilities
----------------
* POST ``/auth/token`` to exchange client credentials for an access token.
* Re-authenticate (single-flight) when the token is missing or expired.
* Expose the current bearer token via :meth:`token` (blocks callers while a
  refresh is in flight — at most ONE refresh runs at a time).
* **Session mode** (``code`` present): two-step exchange — cc-bearer via
  ``/auth/token`` then customer token via ``/biometrics/session-exchange``.
  Single-use ``code`` means no refresh; raises ``SessionTokenExpiredError``
  when the customer token is gone.

Token Modes
-----------
* **Partner mode** (``code=None``, default): standard OAuth2
  ``client_credentials`` — cc-bearer obtained and refreshed as needed.
* **Session mode** (``code`` provided): two-step on the *first* call only.
  Step 1 — cc-bearer (as in partner mode, never exposed to callers).
  Step 2 — ``POST /biometrics/session-exchange`` with the cc-bearer and the
  ``code`` → customer-scoped bearer cached until expiry.  Expiry raises
  ``SessionTokenExpiredError`` (no re-exchange; code is single-use).

Thread Safety
-------------
``threading.Lock`` guards writes to ``_token`` / ``_expires_at``.
A ``threading.Condition`` lets threads that arrive during a refresh wait
without spinning. The ``_refreshing`` flag implements the single-flight
pattern: only the first waiter starts the network call; the rest wait on the
``Condition`` and read the result when it signals.

No async support in v1 (D3 decision: sync-only). The async split is
mechanical when needed.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

#: Seconds before the token's nominal expiry to treat it as already expired.
#:
#: 30 s is intentional (the architecture spec suggested 300 s / 5 min, but that
#: is excessive for a ~1-hour token). The 401 one-shot re-auth in ``SyncHttpClient``
#: is the safety net for actual expiry races; the buffer only needs to cover
#: clock-skew and network latency, for which 30 s is ample. A 5-minute buffer
#: would cause unnecessary pre-emptive refreshes on every call that lands within
#: the last 5 minutes of a token's lifetime.
EXPIRY_BUFFER_SECONDS: float = 30.0

#: Dinie auth token endpoint path (relative to base URL).
TOKEN_PATH = "/auth/token"

#: Session-exchange endpoint path (relative to base URL).
#: Used in session mode (``code`` present) for the second step of the two-step
#: exchange.  Runtime hand-written constant — peer of ``TOKEN_PATH``.
SESSION_EXCHANGE_PATH = "/biometrics/session-exchange"


class TokenManager:
    """Manages a single Dinie access-token lifecycle.

    Supports two modes selected at construction time:

    * **Partner mode** (``code=None``): standard OAuth2 ``client_credentials``.
      The cc-bearer is refreshed transparently whenever it expires.
    * **Session mode** (``code`` provided): two-step exchange on the first call.
      The customer-scoped bearer is cached until expiry; expiry raises
      ``SessionTokenExpiredError`` instead of re-exchanging (code is single-use).

    Args:
        client_id: OAuth client ID.
        client_secret: OAuth client secret.
        base_url: API base URL (no trailing slash).
        http_client: Shared ``httpx.Client`` used to POST the token endpoints.
        code: Bootstrap code for session mode (``dinie_bsc_…``).  When
            ``None`` (default), partner mode is used.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        http_client: httpx.Client,
        *,
        code: str | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client
        self._code = code

        # Session-mode flag: distinguishes "exchange not yet done" (False) from
        # "exchange succeeded once and the token has since expired" (True).
        # In partner mode _exchanged is never read (code is None).
        self._exchanged: bool = False

        self._token: str | None = None
        self._expires_at: float = 0.0  # monotonic timestamp
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._refreshing = False

    @property
    def token(self) -> str:
        """Return the current access token, refreshing if needed.

        In **partner mode**, transparently re-authenticates when the token is
        missing or expired (single-flight).

        In **session mode**, performs the two-step exchange on the first call
        (single-flight); serves subsequent calls from cache.  When the customer
        token expires (or is invalidated by a 401), raises
        ``SessionTokenExpiredError`` instead of re-exchanging.

        Returns:
            A valid bearer token string.

        Raises:
            ``SessionTokenExpiredError``: session mode, token expired (T5).
            ``ApiError``-family: HTTP error from ``/auth/token`` or
                ``/biometrics/session-exchange`` (T9 for invalid codes).
        """
        with self._condition:
            # Fast path: unexpired token
            if self._token is not None and time.monotonic() < self._expires_at:
                return self._token

            # Single-flight: wait if another thread is refreshing
            if self._refreshing:
                self._condition.wait_for(lambda: not self._refreshing)
                # After waking up the token should be set (or _fetch_token raised
                # and the except block cleared _refreshing + re-raised, but in
                # that case wait_for would not have returned normally — the
                # exception path notifies waiters via notify_all in the except).
                if self._token is not None:
                    return self._token
                # Shouldn't happen, but guard against spurious wakeups
                raise RuntimeError("Token refresh completed but token is still unset")

            # This thread owns the refresh
            self._refreshing = True

        # Do the network call OUTSIDE the lock to avoid blocking other threads
        # on the I/O itself. We call notify_all after writing the result.
        try:
            token, expires_in = self._fetch_token()
        except Exception:
            with self._condition:
                self._refreshing = False
                self._condition.notify_all()
            raise

        with self._condition:
            self._token = token
            self._expires_at = time.monotonic() + float(expires_in) - EXPIRY_BUFFER_SECONDS
            self._refreshing = False
            self._condition.notify_all()

        return token

    def invalidate(self) -> None:
        """Force the next :attr:`token` access to re-authenticate.

        Called by the transport layer after a 401 response to trigger a
        one-shot re-auth (D10 behaviour).

        In **partner mode**, the next :attr:`token` call re-fetches a fresh
        cc-bearer.

        In **session mode**, the ``_exchanged`` flag is preserved: if a
        successful exchange was already done (``_exchanged=True``), the next
        :attr:`token` call raises ``SessionTokenExpiredError`` instead of
        attempting a second exchange (which would fail — the code is
        single-use).
        """
        with self._lock:
            self._token = None
            self._expires_at = 0.0

    # ------------------------------------------------------------------
    # Internal fetch helpers (run outside the lock)
    # ------------------------------------------------------------------

    def _fetch_token(self) -> tuple[str, int]:
        """Select the fetch strategy (partner vs session) and return a token.

        Partner mode  — delegates directly to :meth:`_fetch_client_credentials_token`.
        Session mode  — two-step: cc-bearer → ``/biometrics/session-exchange``.
                        Raises ``SessionTokenExpiredError`` if the exchange was
                        already done (code is single-use; no refresh possible).

        Returns:
            ``(access_token, expires_in)`` for the bearer to cache.

        Raises:
            ``SessionTokenExpiredError``: session mode, exchange already done.
            ``ApiError``-family: HTTP error from either endpoint.
        """
        if self._code is None:
            # Partner mode — unchanged behaviour.
            return self._fetch_client_credentials_token()

        # Session mode: two-step exchange.
        if self._exchanged:
            from dinie.runtime.errors import SessionTokenExpiredError

            raise SessionTokenExpiredError(
                "Customer session token has expired. "
                "Obtain a fresh code (new session URL) and construct a new Dinie(code=…) instance."
            )

        # Step 1 — cc-bearer (used only to authenticate the exchange).
        cc_token, _ = self._fetch_client_credentials_token()

        # Step 2 — customer token via session-exchange.
        access_token, expires_in = self._exchange(cc_token, self._code)

        # Mark as exchanged AFTER the exchange succeeds so that a failure in
        # step 2 leaves _exchanged=False (T9: a future call can retry the
        # exchange, which will fail again with the same error — no phantom token).
        self._exchanged = True
        return access_token, expires_in

    def _fetch_client_credentials_token(self) -> tuple[str, int]:
        """POST ``/auth/token`` and return ``(access_token, expires_in)``.

        Returns:
            A ``(access_token, expires_in)`` tuple where ``expires_in`` is
            the lifetime in seconds (integer from the JSON body).

        Raises:
            ``DinieError``-family exceptions propagated from the HTTP layer.
        """
        from dinie.runtime.errors import ApiError, from_response

        url = f"{self._base_url}{TOKEN_PATH}"
        response = self._http_client.post(
            url,
            json={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )

        if response.status_code >= 400:
            try:
                body: object = response.json()
            except Exception:
                body = response.text
            raise from_response(
                status=response.status_code,
                body=body,
                headers=dict(response.headers),
            )

        data: dict[str, object] = response.json()

        access_token = data.get("access_token")
        expires_in = data.get("expires_in")

        if not isinstance(access_token, str) or not access_token:
            raise ApiError(
                "Token response missing 'access_token'",
                status=200,
                body=data,
                headers=dict(response.headers),
            )
        if not isinstance(expires_in, int) or expires_in <= 0:
            # Default to 55 minutes if the field is missing or zero (shouldn't happen)
            expires_in = 3300

        return access_token, expires_in

    def _exchange(self, cc_token: str, code: str) -> tuple[str, int]:
        """POST ``/biometrics/session-exchange`` and return ``(access_token, expires_in)``.

        Called **step 2** of the session-mode exchange.  The cc-bearer obtained
        in step 1 must be passed as ``cc_token``; ``code`` is the single-use
        bootstrap code from the constructor.

        Args:
            cc_token: The cc-bearer from step 1 (``POST /auth/token``).
            code: The ``dinie_bsc_…`` bootstrap code.

        Returns:
            A ``(access_token, expires_in)`` tuple for the customer-scoped bearer.

        Raises:
            ``AuthenticationError`` (401) / ``PermissionDeniedError`` (403)
                from ``from_response`` when the code is invalid or already consumed
                (T9 — DD-5: no new class, token-agnostic error routing).
            ``ApiError``-family: any other HTTP error from the exchange endpoint.
        """
        from dinie.runtime.errors import ApiError, from_response

        url = f"{self._base_url}{SESSION_EXCHANGE_PATH}"
        response = self._http_client.post(
            url,
            headers={"Authorization": f"Bearer {cc_token}"},
            json={"code": code},
        )

        if response.status_code >= 400:
            try:
                body: object = response.json()
            except Exception:
                body = response.text
            raise from_response(
                status=response.status_code,
                body=body,
                headers=dict(response.headers),
            )

        data: dict[str, object] = response.json()

        access_token = data.get("access_token")
        expires_in = data.get("expires_in")

        if not isinstance(access_token, str) or not access_token:
            raise ApiError(
                "Session exchange response missing 'access_token'",
                status=200,
                body=data,
                headers=dict(response.headers),
            )
        if not isinstance(expires_in, int) or expires_in <= 0:
            expires_in = 3300

        return access_token, expires_in
