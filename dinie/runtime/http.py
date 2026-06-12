"""HTTP transport layer for the Dinie Python SDK.

This module provides:

* ``BaseClient[_HttpxClientT]`` — generic base (D3).  Carries all business
  logic: ``request()`` retry loop, ``_build_headers()``, idempotency injection,
  401 one-shot re-auth.  The only abstract method is ``_raw_request()``.
* ``SyncHttpClient`` — concrete sync implementation (``httpx.Client``).
  Overrides **only** ``_raw_request()`` (~12 lines of I/O).

The split is intentional (architecture D3): adding ``AsyncHttpClient`` later
means overriding only ``_raw_request()`` — the retry loop, headers, and
idempotency are inherited unchanged.

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
* Async support (sync-only, D3; the split is mechanical — only ``_raw_request``
  changes).
* Cancellation tokens (D8: ``httpx.Timeout`` per-request covers v1).
"""

from __future__ import annotations

import importlib.metadata
import sys
import time
from typing import Any, Generic, TypeVar

import httpx

from dinie.generated._api_version import API_VERSION as _API_VERSION
from dinie.runtime.errors import APIConnectionError, ApiError, APITimeoutError, from_response
from dinie.runtime.idempotency import generate_key
from dinie.runtime.models import serialize_request
from dinie.runtime.multipart import MultipartBody
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

# ── User-Agent ────────────────────────────────────────────────────────────────
# sdk_version ← installed package metadata (PEP 566); falls back to dev sentinel
# so source-tree runs don't crash before the package is installed.
# api_version ← generated constant (dinie.generated._api_version.API_VERSION);
# updated by `generate` whenever info.version changes — never hardcoded.
try:
    _SDK_VERSION: str = importlib.metadata.version("dinie-sdk")
except importlib.metadata.PackageNotFoundError:
    _SDK_VERSION = "0.0.0+dev"

_PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
_USER_AGENT = (
    f"Dinie-SDK-Python/{_SDK_VERSION} (api-version={_API_VERSION}; python/{_PYTHON_VERSION})"
)


class BaseClient(Generic[_HttpxClientT]):
    """Generic transport base shared by sync (and future async) clients.

    **D3 contract:** this class carries all *pure* business logic — the retry
    loop, header assembly, idempotency injection, and 401 one-shot re-auth.
    Sub-classes implement **only** ``_raw_request()`` (the I/O leaf).

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | MultipartBody | None = None,
        query: dict[str, Any] | None = None,
        request_options: RequestOptions | dict[str, Any] | None = None,
    ) -> Any:
        """Execute an API call with retry / auth / idempotency handling.

        **All** retry logic, header merging, and 401 re-auth live here so that
        sub-classes only need to override ``_raw_request()`` (D3).

        Args:
            method: HTTP verb (uppercase: ``"GET"``, ``"POST"``, …).
            path: URL path, e.g. ``"/v1/credit-offers"``.
            body: Request body — either a plain dict (OMIT-filtered and
                JSON-encoded) or a ``MultipartBody`` instance
                (encoded as ``multipart/form-data`` by the transport).
            query: URL query parameters. ``None`` values are omitted.
            request_options: Per-call overrides (``RequestOptions``, dict, or
                ``None``).

        Returns:
            Parsed JSON response body (dict, list, …) or ``None`` for 204
            responses.

        Raises:
            ``ApiError`` (or a subclass) for every non-2xx response after
            retries.
        """
        opts = RequestOptions.coerce(request_options)
        max_retries = (
            opts.max_retries if opts.max_retries is not None else self._default_max_retries
        )
        timeout = opts.timeout if opts.timeout is not None else self._default_timeout
        extra_headers: dict[str, str | None] = dict(opts.headers or {})

        # Mint the idempotency key once — reused across all retry attempts so
        # that retries never create a duplicate resource.
        idempotency_key: str | None
        if method.upper() in IDEMPOTENT_METHODS:
            idempotency_key = opts.idempotency_key or generate_key()
        else:
            idempotency_key = None

        # Multipart bodies pass through un-serialised; dicts are OMIT-filtered.
        body_to_send: dict[str, Any] | MultipartBody | None
        if isinstance(body, MultipartBody):
            body_to_send = body
        elif body is not None:
            body_to_send = serialize_request(body)
        else:
            body_to_send = None

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
                body=body_to_send,
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
                continue  # retry immediately, no sleep, attempt counter unchanged

            # Retryable status + budget remains → sleep and retry
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
        # were consumed by the one-shot 401 re-auth.
        raise ApiError(
            "Exhausted retry attempts",
            status=0,
            body=None,
            headers={},
        )

    # ------------------------------------------------------------------
    # Pure helpers (no I/O)
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

        A ``None`` value in ``extra_headers`` removes the corresponding default
        header (mirrors Ruby's ``nil``-to-remove behaviour).

        Args:
            token: Bearer token for the ``Authorization`` header.
            extra_headers: Per-call overrides from ``RequestOptions.headers``.
            idempotency_key: Idempotency key, or ``None`` for non-idempotent
                methods.
            retry_count: Current attempt index; ``> 0`` → inject
                ``X-Dinie-Retry-Count``.

        Returns:
            A headers dict with string keys and string values.
        """
        merged: dict[str, str | None] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }
        if idempotency_key is not None:
            merged["Idempotency-Key"] = idempotency_key
        if retry_count > 0:
            merged["X-Dinie-Retry-Count"] = str(retry_count)
        # Apply per-call overrides last; None removes the key
        merged.update(extra_headers)
        return {k: v for k, v in merged.items() if v is not None}

    # ------------------------------------------------------------------
    # I/O leaf — MUST be overridden by sub-classes
    # ------------------------------------------------------------------

    def _raw_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, Any] | MultipartBody | None,
        params: dict[str, str] | None,
        timeout: float,
    ) -> httpx.Response:
        """Issue the raw HTTP request.

        **D3 extension point.** ``BaseClient.request()`` calls this for every
        attempt; sub-classes swap in the transport without touching any retry or
        header logic.

        Args:
            method: HTTP verb.
            url: Fully-qualified URL.
            headers: Merged request headers (includes ``Content-Type:
                application/json`` for plain dict bodies; the transport
                strips it for ``MultipartBody`` so ``httpx`` can set the
                multipart boundary).
            body: Serialised JSON body (plain dict or ``None``) **or** a
                ``MultipartBody`` instance to encode as
                ``multipart/form-data``.
            params: URL query parameters (or ``None``).
            timeout: Request timeout in seconds.

        Returns:
            The raw ``httpx.Response``.

        Raises:
            ``NotImplementedError`` — sub-classes must override.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement _raw_request()")


class SyncHttpClient(BaseClient[httpx.Client]):
    """Synchronous HTTP client built on ``httpx.Client``.

    Instantiated by the generated ``Dinie()`` constructor (story 007). Users
    never construct this directly.

    **D3:** this class overrides **only** ``_raw_request()`` (~12 lines of I/O).
    The retry loop, header assembly, idempotency injection, and 401 re-auth are
    all inherited from ``BaseClient``.
    """

    def _raw_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, Any] | MultipartBody | None,
        params: dict[str, str] | None,
        timeout: float,
    ) -> httpx.Response:
        """Delegate the raw HTTP call to the underlying ``httpx.Client``.

        Routes ``MultipartBody`` instances through ``httpx``'s
        ``files=`` / ``data=`` encoding path (sets
        ``Content-Type: multipart/form-data; boundary=…``); plain dicts
        go through the ``json=`` path (``Content-Type: application/json``).

        ``httpx.TimeoutException`` (``ConnectTimeout``, ``ReadTimeout``,
        ``WriteTimeout``, ``PoolTimeout``) is translated to
        ``APITimeoutError``; ``httpx.ConnectError`` is translated to
        ``APIConnectionError``.  The original exception is chained via
        ``__cause__``.
        """
        try:
            if isinstance(body, MultipartBody):
                # Build httpx files= / data= args.
                # files= (even when empty) triggers multipart/form-data encoding;
                # httpx appends the boundary automatically.
                httpx_files: dict[str, tuple[str, bytes | Any, str]] = {}
                if body.file is not None:
                    httpx_files["file"] = (
                        body.file_name,
                        body.file,
                        body.file_content_type,
                    )
                # Strip Content-Type: application/json — httpx sets the multipart one.
                mp_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
                return self._http.request(
                    method,
                    url,
                    headers=mp_headers,
                    data=dict(body.fields) if body.fields else None,
                    files=httpx_files,
                    params=params,
                    timeout=timeout,
                )
            return self._http.request(
                method,
                url,
                headers=headers,
                json=body,
                params=params,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(str(e) or "Request timed out") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(str(e) or "Connection error") from e
