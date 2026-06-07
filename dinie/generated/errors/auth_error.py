# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class AuthError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/authentication-failed"""

    status_code: int = 401
