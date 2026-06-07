# generated — do not edit
from __future__ import annotations

from ...runtime.errors import ApiError


class PermissionDeniedError(ApiError):
    """RFC 9457 type: https://docs.dinie.com/errors/forbidden"""

    status_code: int = 403
