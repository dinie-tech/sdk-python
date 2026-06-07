# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class NotFoundError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/not-found"""

    status_code: int = 404
