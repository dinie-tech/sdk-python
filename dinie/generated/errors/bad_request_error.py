# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class BadRequestError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/invalid-request"""

    status_code: int = 400
