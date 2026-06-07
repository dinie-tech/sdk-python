# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class ValidationError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/validation-failed"""

    status_code: int = 422
