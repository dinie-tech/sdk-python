# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class RateLimitError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/rate-limit-exceeded"""

    status_code: int = 429
