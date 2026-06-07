# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class ServerError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/internal"""

    status_code: int = 500
