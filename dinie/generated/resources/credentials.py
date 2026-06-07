# generated — do not edit
from __future__ import annotations

from ...runtime.http import SyncHttpClient
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.create_credential_request import CreateCredentialRequest
from ..types.credential import Credential
from ..types.credential_with_secret import CredentialWithSecret


class Credentials:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        params: CreateCredentialRequest,
        request_options: RequestOptions | None = None,
    ) -> CredentialWithSecret:
        raw = self._http.request(
            "POST",
            "/auth/credentials",
            body=CreateCredentialRequest.serialize_create(params),
            request_options=request_options,
        )
        return CredentialWithSecret.deserialize(raw)

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[Credential]:
        raw = self._http.request("GET", "/auth/credentials", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=Credential.deserialize)

    def revoke(
        self,
        client_id: str,
        request_options: RequestOptions | None = None,
    ) -> None:
        self._http.request(
            "DELETE", f"/auth/credentials/{client_id}", request_options=request_options
        )
