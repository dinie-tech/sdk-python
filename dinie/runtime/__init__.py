"""Dinie SDK runtime layer — hand-written, do not regenerate.

This package contains the hand-written infrastructure: HTTP client, token
management, retry logic, pagination, error hierarchy, webhook verification,
logging, idempotency, and rate-limit tracking.

Public surface (story 003)
--------------------------
* ``OMIT`` / ``OmitType`` / ``Model`` / ``serialize_request`` — model utilities
* ``RequestOptions`` — per-call transport overrides
* ``RateLimit`` / ``RateLimitTracker`` — rate-limit header parsing
* ``generate_key`` / ``KEY_PREFIX`` — idempotency key generation
* ``should_retry`` / ``retry_delay`` / ``parse_retry_after`` — retry helpers
* ``RETRYABLE_STATUS`` / ``RETRY_AFTER_CAP_SECONDS`` — retry constants
* ``DinieError`` / ``ApiError`` / named status errors — exception hierarchy
* ``ERROR_REGISTRY`` / ``register_error`` / ``from_response`` — error registry
* ``TokenManager`` — bearer-token lifecycle (single-flight refresh)
* ``SyncHttpClient`` / ``BaseClient`` — HTTP transport
* ``DEFAULT_BASE_URL`` / ``DEFAULT_MAX_RETRIES`` / ``DEFAULT_TIMEOUT`` — defaults
"""

from dinie.runtime.errors import (
    ERROR_REGISTRY,
    ApiError,
    AuthenticationError,
    BadGatewayError,
    ConflictError,
    DinieError,
    GatewayTimeoutError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    from_response,
    register_error,
)
from dinie.runtime.http import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    IDEMPOTENT_METHODS,
    BaseClient,
    SyncHttpClient,
)
from dinie.runtime.idempotency import KEY_PREFIX, generate_key
from dinie.runtime.models import OMIT, Model, OmitType, serialize_request
from dinie.runtime.rate_limit import RateLimit, RateLimitTracker
from dinie.runtime.request_options import RequestOptions
from dinie.runtime.retry import (
    INITIAL_BACKOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    RETRY_AFTER_CAP_SECONDS,
    RETRYABLE_STATUS,
    parse_retry_after,
    retry_delay,
    should_retry,
)
from dinie.runtime.token_manager import EXPIRY_BUFFER_SECONDS, TOKEN_PATH, TokenManager

__all__ = [
    # models
    "OMIT",
    "OmitType",
    "Model",
    "serialize_request",
    # request options
    "RequestOptions",
    # rate limit
    "RateLimit",
    "RateLimitTracker",
    # idempotency
    "KEY_PREFIX",
    "generate_key",
    # retry
    "INITIAL_BACKOFF_SECONDS",
    "MAX_BACKOFF_SECONDS",
    "RETRY_AFTER_CAP_SECONDS",
    "RETRYABLE_STATUS",
    "parse_retry_after",
    "retry_delay",
    "should_retry",
    # errors
    "ApiError",
    "AuthenticationError",
    "BadGatewayError",
    "ConflictError",
    "DinieError",
    "ERROR_REGISTRY",
    "GatewayTimeoutError",
    "InternalServerError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServiceUnavailableError",
    "UnprocessableEntityError",
    "from_response",
    "register_error",
    # token manager
    "EXPIRY_BUFFER_SECONDS",
    "TOKEN_PATH",
    "TokenManager",
    # http
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT",
    "IDEMPOTENT_METHODS",
    "BaseClient",
    "SyncHttpClient",
]
