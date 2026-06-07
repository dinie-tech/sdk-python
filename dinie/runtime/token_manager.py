"""Token-lifecycle manager for the Dinie Python SDK.

Responsibilities
----------------
* POST ``/auth/token`` to exchange client credentials for an access token.
* Re-authenticate (single-flight) when the token is missing or expired.
* Expose the current bearer token via :meth:`token` (blocks callers while a
  refresh is in flight — at most ONE refresh runs at a time).

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


class TokenManager:
    """Manages a single Dinie access-token lifecycle.

    Args:
        client_id: OAuth client ID.
        client_secret: OAuth client secret.
        base_url: API base URL (no trailing slash).
        http_client: Shared ``httpx.Client`` used to POST the token endpoint.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        http_client: httpx.Client,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client

        self._token: str | None = None
        self._expires_at: float = 0.0  # Unix timestamp
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._refreshing = False

    @property
    def token(self) -> str:
        """Return the current access token, refreshing if needed.

        Blocks until a valid token is available. Only one thread issues the
        refresh call; others wait on the ``Condition`` and read the result.

        Returns:
            A valid bearer token string.

        Raises:
            ``ApiError``-family exceptions (re-raised from the HTTP call).
        """
        with self._condition:
            # Fast path: unexpired token
            if self._token is not None and time.monotonic() < self._expires_at:
                return self._token

            # Single-flight: wait if another thread is refreshing
            if self._refreshing:
                self._condition.wait_for(lambda: not self._refreshing)
                # After waking up the token should be set
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
        """
        with self._lock:
            self._token = None
            self._expires_at = 0.0

    def _fetch_token(self) -> tuple[str, int]:
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
