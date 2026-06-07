# generated — do not edit
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...runtime.errors import ApiError

from .auth_error import AuthError
from .bad_request_error import BadRequestError
from .conflict_error import ConflictError
from .not_found_error import NotFoundError
from .permission_denied_error import PermissionDeniedError
from .rate_limit_error import RateLimitError
from .server_error import ServerError
from .validation_error import ValidationError

# Registry: type-URL → error class (RFC 9457 `type` field)
ERROR_REGISTRY_BY_TYPE: dict[str, type[ApiError]] = {
    "https://docs.dinie.com/errors/authentication-failed": AuthError,
    "https://docs.dinie.com/errors/invalid-request": BadRequestError,
    "https://docs.dinie.com/errors/conflict": ConflictError,
    "https://docs.dinie.com/errors/not-found": NotFoundError,
    "https://docs.dinie.com/errors/forbidden": PermissionDeniedError,
    "https://docs.dinie.com/errors/rate-limit-exceeded": RateLimitError,
    "https://docs.dinie.com/errors/internal": ServerError,
    "https://docs.dinie.com/errors/validation-failed": ValidationError,
}

# Registry: HTTP status → error class (fallback when no type URL matches)
ERROR_REGISTRY_BY_STATUS: dict[int, type[ApiError]] = {
    400: BadRequestError,
    401: AuthError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
    500: ServerError,
}

# Fallback for unmatched 5xx responses
SERVER_ERROR_CLASS: type[ApiError] = ServerError

__all__ = [
    "BadRequestError",
    "AuthError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "ERROR_REGISTRY_BY_TYPE",
    "ERROR_REGISTRY_BY_STATUS",
    "SERVER_ERROR_CLASS",
]
