# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class ConflictError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/conflict"""

    status_code: int = 409
