# generated — do not edit
from __future__ import annotations

from typing import Any

from ...runtime.http import SyncHttpClient
from ...runtime.request_options import RequestOptions
from ..types.biometrics_session_exchange_response import BiometricsSessionExchangeResponse


class Biometrics:
    """Biometrics resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def session_exchange(
        self,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> BiometricsSessionExchangeResponse:
        """
        Exchange a biometrics bootstrap code for a session token

        Internal endpoint — the kyc-app calls this with a credential that only has the `biometrics:exchange` scope, swapping the single-use bootstrap code (`dinie_bsc_…`) for a Token bound to the session's CreditLineApplication. The token is the bearer the wizard uses for every subsequent KYC request.

        :param params: Request parameters.
        """
        raw = self._http.request(
            "POST", "/biometrics/session-exchange", body=params, request_options=request_options
        )
        return BiometricsSessionExchangeResponse.deserialize(raw)
