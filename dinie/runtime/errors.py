"""Error hierarchy and response-to-exception dispatcher for the Dinie Python SDK.

Design
------
* ``DinieError`` — base; every public exception inherits from it.
* ``APIConnectionError`` — network-level error (no HTTP response).
* ``APITimeoutError`` — timeout before receiving a response (sub of APIConnectionError).
* ``ApiError`` — carries ``status``, ``body``, ``headers`` from a non-2xx response.
* ``AuthenticationError`` (401), ``PermissionDeniedError`` (403),
  ``NotFoundError`` (404), ``ConflictError`` (409), ``UnprocessableEntityError`` (422),
  ``RateLimitError`` (429) — named wrappers for the most common statuses.
* ``InternalServerError`` (500), ``BadGatewayError`` (502), ``ServiceUnavailableError``
  (503), ``GatewayTimeoutError`` (504) — server-side errors.
* ``ERROR_REGISTRY`` — a ``dict[str, type[ApiError]]`` keyed by the ``type`` URL found
  in the response body.  Generated ``dinie/generated/errors/*.py`` modules register
  domain-specific subclasses via ``register_error(url, cls)``.
* ``from_response`` — the single dispatcher used by the transport layer.

Keeping domain-specific error classes in ``generated/errors/`` and using
``ERROR_REGISTRY`` avoids circular imports: runtime doesn't know about generated code,
but generated modules import from runtime and side-effectfully populate the registry.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Base exceptions
# ---------------------------------------------------------------------------


class DinieError(Exception):
    """Base class for every exception raised by the Dinie SDK.

    Catch this to handle all SDK errors uniformly. Use a subclass for narrower
    handling (e.g. ``except RateLimitError``).
    """


class APIConnectionError(DinieError):
    """Network-level error — the request did not receive an HTTP response.

    Raised when a transport exception (connection refused, DNS failure, etc.)
    prevents the request from reaching the server.  The original
    ``httpx`` exception is available as ``__cause__``.

    Subclasses: ``APITimeoutError``.
    """


class APITimeoutError(APIConnectionError):
    """The request timed out before receiving an HTTP response.

    Raised when ``httpx.TimeoutException`` (any of ``ConnectTimeout``,
    ``ReadTimeout``, ``WriteTimeout``, ``PoolTimeout``) escapes the transport.
    The original ``httpx`` exception is available as ``__cause__``.
    """


class ApiError(DinieError):
    """A non-2xx HTTP response from the Dinie API.

    Attributes:
        status: HTTP status code.
        body: Parsed response body (dict, list, str, …) or ``None`` when the
            response body is empty or could not be decoded.
        headers: Response headers mapping.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        body: Any,
        headers: dict[str, str],
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body
        self.headers = headers

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status={self.status!r}, message={str(self)!r})"


# ---------------------------------------------------------------------------
# Named-status subclasses
# ---------------------------------------------------------------------------


class AuthenticationError(ApiError):
    """HTTP 401 — missing or invalid credentials."""


class PermissionDeniedError(ApiError):
    """HTTP 403 — credentials are valid but lack permission."""


class NotFoundError(ApiError):
    """HTTP 404 — resource does not exist."""


class ConflictError(ApiError):
    """HTTP 409 — idempotency-key reuse or state-machine conflict."""


class UnprocessableEntityError(ApiError):
    """HTTP 422 — request body is structurally valid but semantically rejected."""


class RateLimitError(ApiError):
    """HTTP 429 — too many requests; inspect ``Retry-After`` for the wait time."""


class InternalServerError(ApiError):
    """HTTP 5xx — the API returned a server-side error."""


class BadGatewayError(ApiError):
    """HTTP 502 — bad gateway."""


class ServiceUnavailableError(ApiError):
    """HTTP 503 — service temporarily unavailable."""


class GatewayTimeoutError(ApiError):
    """HTTP 504 — gateway timeout."""


# ---------------------------------------------------------------------------
# Status-to-class table (for statuses not covered by ERROR_REGISTRY)
# ---------------------------------------------------------------------------

_STATUS_MAP: dict[int, type[ApiError]] = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}

# ---------------------------------------------------------------------------
# ERROR_REGISTRY — populated by generated/errors/* at import time
# ---------------------------------------------------------------------------

#: Maps a ``type`` URL from the RFC-7807 problem body to the subclass that
#: should be raised.  Generated error modules populate this at import time via
#: ``register_error``.
ERROR_REGISTRY: dict[str, type[ApiError]] = {}


def register_error(type_url: str, cls: type[ApiError]) -> None:
    """Register a generated error class.

    Called by ``dinie/generated/errors/<name>.py`` at module import time.

    Args:
        type_url: The ``type`` field from the RFC-7807 problem body,
            e.g. ``"https://errors.dinie.com.br/insufficient-balance"``.
        cls: Subclass of ``ApiError`` to raise when this URL is encountered.
    """
    ERROR_REGISTRY[type_url] = cls


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def from_response(
    *,
    status: int,
    body: Any,
    headers: dict[str, str],
) -> ApiError:
    """Build the most-specific ``ApiError`` for an error response.

    Resolution order:

    1. If ``body`` is a dict with a ``"type"`` key that matches an entry in
       ``ERROR_REGISTRY``, use the registered class.
    2. If ``status`` is in ``_STATUS_MAP``, use the named subclass.
    3. If ``status >= 500``, use ``InternalServerError``.
    4. Fallback: plain ``ApiError``.

    Args:
        status: HTTP status code.
        body: Parsed response body.
        headers: Response headers.

    Returns:
        An ``ApiError`` instance (never raises).
    """
    message = _extract_message(status, body)

    # 1. Type-URL in registry
    if isinstance(body, dict):
        type_url = body.get("type")
        if isinstance(type_url, str) and type_url in ERROR_REGISTRY:
            return ERROR_REGISTRY[type_url](message, status=status, body=body, headers=headers)

    # 2. Named status
    if status in _STATUS_MAP:
        return _STATUS_MAP[status](message, status=status, body=body, headers=headers)

    # 3. Generic 5xx
    if status >= 500:
        return InternalServerError(message, status=status, body=body, headers=headers)

    # 4. Fallback
    return ApiError(message, status=status, body=body, headers=headers)


def _extract_message(status: int, body: Any) -> str:
    """Build a human-readable error message from the response body."""
    if isinstance(body, dict):
        for key in ("detail", "message", "error", "title"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
    if isinstance(body, str) and body:
        return body
    return f"HTTP {status}"
