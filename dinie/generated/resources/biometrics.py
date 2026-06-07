# generated — do not edit
from __future__ import annotations

from typing import Any

from ...runtime.http import SyncHttpClient
from ...runtime.request_options import RequestOptions
from ..types.biometrics_session_exchange_response import BiometricsSessionExchangeResponse


class Biometrics:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def session_exchange(
        self,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> BiometricsSessionExchangeResponse:
        raw = self._http.request(
            "POST", "/biometrics/session-exchange", body=params, request_options=request_options
        )
        return BiometricsSessionExchangeResponse.deserialize(raw)
