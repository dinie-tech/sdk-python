"""Dinie SDK runtime layer — hand-written, do not regenerate.

This package contains the hand-written infrastructure: HTTP client, token
management, retry logic, pagination, error hierarchy, webhook verification,
logging, idempotency, and rate-limit tracking.

Public surface (story 003 + 004 + 012 + 013)
---------------------------------------------
Story 003 — transport spine:
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

Story 004 — domain layer:
* ``extract`` — Standard Webhooks v1 verify + dispatch
* ``WebhookError`` / ``WebhookSignatureError`` / ``WebhookTimestampError``
  / ``UnknownWebhookEventError`` — webhook exceptions
* ``EVENT_DESERIALIZERS`` / ``register_event`` — webhook event registry
* ``SyncCursorPage`` — cursor-paginated results (``has_more``-driven)
* ``SensitiveDataFilter`` / ``setup_logging`` / ``get_logger`` / ``redact_headers``
  / ``redact_body`` — logging infrastructure

Story 012 — C1-PY-1 (typed transport exceptions):
* ``APIConnectionError`` — network-level error (no HTTP response)
* ``APITimeoutError`` — timeout subclass of ``APIConnectionError``

Story 013 — multipart transport:
* ``MultipartBody`` — ``multipart/form-data`` body (fields + optional file)

Story 015a — session mode:
* ``SessionTokenExpiredError`` — customer token expired (no refresh in session mode)
* ``SESSION_EXCHANGE_PATH`` — session-exchange endpoint constant
"""

from dinie.runtime.errors import (
    ERROR_REGISTRY,
    APIConnectionError,
    ApiError,
    APITimeoutError,
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
    SessionTokenExpiredError,
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
from dinie.runtime.logger import (
    BODY_TRUNCATE_CHARS,
    LOG_ENV_VAR,
    REDACTED,
    SDK_LOGGER_NAME,
    SENSITIVE_BODY_KEYS,
    SENSITIVE_HEADERS,
    SensitiveDataFilter,
    get_logger,
    redact_body,
    redact_headers,
    setup_logging,
)
from dinie.runtime.models import OMIT, Model, OmitType, serialize_request
from dinie.runtime.multipart import DEFAULT_FILE_CONTENT_TYPE, DEFAULT_FILE_NAME, MultipartBody
from dinie.runtime.paginator import SyncCursorPage
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
from dinie.runtime.token_manager import (
    EXPIRY_BUFFER_SECONDS,
    SESSION_EXCHANGE_PATH,
    TOKEN_PATH,
    TokenManager,
)
from dinie.runtime.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    EVENT_DESERIALIZERS,
    WEBHOOK_ID_HEADER,
    WEBHOOK_SIGNATURE_HEADER,
    WEBHOOK_TIMESTAMP_HEADER,
    UnknownWebhookEventError,
    WebhookError,
    WebhookSignatureError,
    WebhookTimestampError,
    extract,
    register_event,
)

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
    "APIConnectionError",
    "APITimeoutError",
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
    "SessionTokenExpiredError",
    "UnprocessableEntityError",
    "from_response",
    "register_error",
    # token manager
    "EXPIRY_BUFFER_SECONDS",
    "SESSION_EXCHANGE_PATH",
    "TOKEN_PATH",
    "TokenManager",
    # http
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT",
    "IDEMPOTENT_METHODS",
    "BaseClient",
    "SyncHttpClient",
    # multipart (story 013)
    "DEFAULT_FILE_CONTENT_TYPE",
    "DEFAULT_FILE_NAME",
    "MultipartBody",
    # webhooks (story 004)
    "DEFAULT_TOLERANCE_SECONDS",
    "EVENT_DESERIALIZERS",
    "WEBHOOK_ID_HEADER",
    "WEBHOOK_SIGNATURE_HEADER",
    "WEBHOOK_TIMESTAMP_HEADER",
    "UnknownWebhookEventError",
    "WebhookError",
    "WebhookSignatureError",
    "WebhookTimestampError",
    "extract",
    "register_event",
    # paginator (story 004)
    "SyncCursorPage",
    # logger (story 004)
    "BODY_TRUNCATE_CHARS",
    "LOG_ENV_VAR",
    "REDACTED",
    "SDK_LOGGER_NAME",
    "SENSITIVE_BODY_KEYS",
    "SENSITIVE_HEADERS",
    "SensitiveDataFilter",
    "get_logger",
    "redact_body",
    "redact_headers",
    "setup_logging",
]
