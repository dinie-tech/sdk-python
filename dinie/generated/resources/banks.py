# generated — do not edit
from __future__ import annotations

from ...runtime.http import SyncHttpClient
from ...runtime.request_options import RequestOptions
from ..types.bank import Bank


class Banks:
    """Banks resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> Bank:
        """
        List banks

        List banks available for customer bank account submission.
        """
        raw = self._http.request("GET", "/banks", request_options=request_options)
        return Bank.deserialize(raw)
