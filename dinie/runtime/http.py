"""HTTP transport layer for the Dinie Python SDK.

This module provides:

* ``BaseClient[_HttpxClientT]`` — generic base (D3).
* ``SyncHttpClient`` — concrete sync implementation (``httpx.Client``).

Responsibilities
----------------
* Merge per-call ``RequestOptions`` with client-level defaults.
* Manage retry loops: exponential backoff, ``Retry-After`` header, 401 one-shot
  re-auth (via ``TokenManager``).
* Inject auth (``Authorization: Bearer``), ``Idempotency-Key``, and
  ``X-Dinie-Retry-Count`` headers.
* Update the ``RateLimitTracker`` snapshot after every response.
* Raise the appropriate ``ApiError`` subclass via ``from_response``.
* Provide ``with_options()`` cloning that shares the same ``TokenManager``
  and ``httpx.Client`` (D10).

Non-goals (for v1)
------------------
* Async support (sync-only, D3; the split is mechanical).
* Cancellation tokens (D8: ``httpx.Timeout`` per-request covers v1).
"""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

import httpx

from dinie.runtime.errors import ApiError, from_response
from dinie.runtime.idempotency import generate_key
from dinie.runtime.models import serialize_request
from dinie.runtime.rate_limit import RateLimitTracker
from dinie.runtime.request_options import RequestOptions
from dinie.runtime.retry import retry_delay, should_retry
from dinie.runtime.token_manager import TokenManager

_HttpxClientT = TypeVar("_HttpxClientT", bound=httpx.Client)

#: Default base URL (production).
DEFAULT_BASE_URL = "https://api.dinie.com.br"

#: Default number of automatic retries (not counting the initial attempt).
DEFAULT_MAX_RETRIES = 2

#: Default timeout for all requests, in seconds.
DEFAULT_TIMEOUT = 60.0

#: Methods for which the SDK automatically injects a new ``Idempotency-Key``
#: when one isn't supplied explicitly via ``RequestOptions``.
IDEMPOTENT_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})


class BaseClient(Generic[_HttpxClientT]):
    """Generic transport base shared by sync (and future async) clients.

    Sub-classes own the ``_http`` field and override ``_raw_request``.

    Args:
        base_url: API base URL (default: production).
        max_retries: Default maximum retries per request.
        timeout: Default per-request timeout in seconds.
        http_client: The underlying ``httpx.Client`` instance.
        token_manager: Shared ``TokenManager`` for bearer-token lifecycle.
    """

    def __init__(
        self,
        base_url: str,
        max_retries: int,
        timeout: float,
        http_client: _HttpxClientT,
        token_manager: TokenManager,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_max_retries = max_retries
        self._default_timeout = timeout
        self._http = http_client
        self._token_manager = token_manager
        self._rate_limit = RateLimitTracker()

    @property
    def rate_limit(self) -> RateLimitTracker:
        """Rate-limit snapshot tracker updated after every API response."""
        return self._rate_limit

    def with_options(self, **kwargs: Any) -> SyncHttpClient:
        """Return a new client sharing the same ``TokenManager`` and ``httpx.Client``.

        Only accepts ``base_url``, ``max_retries``, ``timeout`` — call-level
        overrides belong in ``RequestOptions``. The underlying HTTP connection
        pool is shared (D10: no extra token POST on clone).

        Args:
            **kwargs: Any subset of ``base_url``, ``max_retries``, ``timeout``.

        Returns:
            A fresh ``SyncHttpClient`` with the overridden defaults.
        """
        return SyncHttpClient(
            base_url=str(kwargs.get("base_url", self._base_url)),
            max_retries=int(kwargs.get("max_retries", self._default_max_retries)),
            timeout=float(kwargs.get("timeout", self._default_timeout)),
            http_client=self._http,
            token_manager=self._token_manager,
        )


class SyncHttpClient(BaseClient[httpx.Client]):
    """Synchronous HTTP client built on ``httpx.Client``.

    Instantiated by the generated ``Dinie()`` constructor (story 007). Users
    never construct this directly.

    The retry loop:

    1. Issue the request.
    2. If 401 → invalidate token → retry ONCE (no backoff, no counter increment).
    3. If in ``RETRYABLE_STATUS`` and attempts remain → sleep → retry.
    4. Otherwise → ``from_response`` → raise.

    ``X-Dinie-Retry-Count: N`` is injected on every retry (N ≥ 1).
    The idempotency key is minted once before the loop so retries reuse it.
    """

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        request_options: RequestOptions | dict[str, Any] | None = None,
    ) -> Any:
        """Execute an API call with retry / auth / idempotency handling.

        Args:
            method: HTTP verb (uppercase: ``"GET"``, ``"POST"``, …).
            path: URL path, e.g. ``"/v1/credit-offers"``.
            body: Request body as a raw dict (OMIT-filtered by ``serialize_request``).
            query: URL query parameters. ``None`` values are omitted.
            request_options: Per-call overrides (``RequestOptions``, dict, or ``None``).

        Returns:
            Parsed JSON response body (dict, list, …) or ``None`` for 204 responses.

        Raises:
            ``ApiError`` (or a subclass) for every non-2xx response after retries.
        """
        opts = RequestOptions.coerce(request_options)
        max_retries = (
            opts.max_retries if opts.max_retries is not None else self._default_max_retries
        )
        timeout = opts.timeout if opts.timeout is not None else self._default_timeout
        extra_headers: dict[str, str | None] = dict(opts.headers or {})

        # Mint the idempotency key once — reused across all retry attempts
        idempotency_key: str | None
        if method.upper() in IDEMPOTENT_METHODS:
            idempotency_key = opts.idempotency_key or generate_key()
        else:
            idempotency_key = None

        serialized_body: dict[str, Any] | None = (
            serialize_request(body) if body is not None else None
        )
        clean_query: dict[str, str] | None = (
            {k: str(v) for k, v in query.items() if v is not None} if query else None
        )

        auth_retry_done = False  # 401 re-auth is a one-shot

        for attempt in range(max_retries + 1):
            token = self._token_manager.token
            headers = self._build_headers(
                token=token,
                extra_headers=extra_headers,
                idempotency_key=idempotency_key,
                retry_count=attempt,
            )

            response = self._raw_request(
                method=method.upper(),
                url=f"{self._base_url}{path}",
                headers=headers,
                json=serialized_body,
                params=clean_query,
                timeout=timeout,
            )

            # Always capture rate-limit info
            self._rate_limit.update(dict(response.headers))

            status = response.status_code

            # 2xx → success
            if 200 <= status < 300:
                if status == 204 or not response.content:
                    return None
                return response.json()

            # 401: one-shot re-auth (does NOT count against retry budget)
            if status == 401 and not auth_retry_done:
                auth_retry_done = True
                self._token_manager.invalidate()
                continue  # retry immediately, no sleep, attempt stays same

            # Retryable + budget remains
            if should_retry(status) and attempt < max_retries:
                delay = retry_delay(
                    attempt,
                    retry_after=response.headers.get("retry-after"),
                    retry_after_ms=response.headers.get("retry-after-ms"),
                )
                time.sleep(delay)
                continue

            # Non-retryable or budget exhausted → raise
            try:
                body_parsed: Any = response.json()
            except Exception:
                body_parsed = response.text or None

            raise from_response(
                status=status,
                body=body_parsed,
                headers=dict(response.headers),
            )

        # Should be unreachable, but guard against the edge where all attempts
        # were 401s consumed by the one-shot re-auth logic.
        raise ApiError(
            "Exhausted retry attempts",
            status=0,
            body=None,
            headers={},
        )

    def _raw_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None,
        params: dict[str, str] | None,
        timeout: float,
    ) -> httpx.Response:
        """Issue the raw HTTP request via the underlying ``httpx.Client``.

        Separated from the retry loop so tests can monkey-patch or override this
        method cleanly.

        Args:
            method: HTTP verb.
            url: Fully-qualified URL.
            headers: Merged request headers.
            json: Serialised request body (or ``None``).
            params: URL query parameters (or ``None``).
            timeout: Request timeout in seconds.

        Returns:
            The raw ``httpx.Response``.
        """
        return self._http.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_headers(
        *,
        token: str,
        extra_headers: dict[str, str | None],
        idempotency_key: str | None,
        retry_count: int,
    ) -> dict[str, str]:
        """Merge all header sources into a final headers dict.

        A ``None`` value in ``extra_headers`` removes the corresponding default header
        (matches Ruby's ``nil``-to-remove behaviour).

        Args:
            token: Bearer token for the ``Authorization`` header.
            extra_headers: Per-call overrides from ``RequestOptions.headers``.
            idempotency_key: Idempotency key, or ``None`` for non-idempotent methods.
            retry_count: Current attempt index; ``> 0`` → inject ``X-Dinie-Retry-Count``.

        Returns:
            A headers dict with string keys and string values.
        """
        merged: dict[str, str | None] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if idempotency_key is not None:
            merged["Idempotency-Key"] = idempotency_key
        if retry_count > 0:
            merged["X-Dinie-Retry-Count"] = str(retry_count)
        # Apply per-call overrides last; None removes the key
        merged.update(extra_headers)
        return {k: v for k, v in merged.items() if v is not None}
