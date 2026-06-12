# generated — do not edit
from __future__ import annotations

from ...runtime.http import SyncHttpClient
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.create_credential_request import CreateCredentialRequest
from ..types.credential import Credential
from ..types.credential_with_secret import CredentialWithSecret


class Credentials:
    """Credentials resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        params: CreateCredentialRequest,
        request_options: RequestOptions | None = None,
    ) -> CredentialWithSecret:
        """
        Create a new API key

        Create a new credential pair; the `client_secret` is shown only once in the response

        :param params: Request parameters.
        """
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
        """
        List API keys

        Return all API credentials for the authenticated partner
        """
        raw = self._http.request("GET", "/auth/credentials", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=Credential.deserialize)

    def revoke(
        self,
        client_id: str,
        request_options: RequestOptions | None = None,
    ) -> None:
        """
        Revoke an API key

        Immediately and permanently revoke an API credential

        :param client_id: Path parameter.
        """
        self._http.request(
            "DELETE", f"/auth/credentials/{client_id}", request_options=request_options
        )
