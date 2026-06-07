# generated — do not edit
from __future__ import annotations

from typing import Any

from ...runtime.http import SyncHttpClient
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.create_webhook_endpoint_request import CreateWebhookEndpointRequest
from ..types.update_webhook_endpoint_request import UpdateWebhookEndpointRequest
from ..types.webhook_endpoint import WebhookEndpoint
from ..types.webhook_endpoint_with_secret import WebhookEndpointWithSecret
from ..types.webhook_secret_rotation import WebhookSecretRotation


class WebhookEndpoints:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        params: CreateWebhookEndpointRequest,
        request_options: RequestOptions | None = None,
    ) -> WebhookEndpointWithSecret:
        raw = self._http.request(
            "POST",
            "/webhooks/endpoints",
            body=CreateWebhookEndpointRequest.serialize_create(params),
            request_options=request_options,
        )
        return WebhookEndpointWithSecret.deserialize(raw)

    def delete(
        self,
        webhook_endpoint_id: str,
        request_options: RequestOptions | None = None,
    ) -> None:
        self._http.request(
            "DELETE", f"/webhooks/endpoints/{webhook_endpoint_id}", request_options=request_options
        )

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookEndpoint]:
        raw = self._http.request("GET", "/webhooks/endpoints", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=WebhookEndpoint.deserialize)

    def retrieve(
        self,
        webhook_endpoint_id: str,
        request_options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        raw = self._http.request(
            "GET", f"/webhooks/endpoints/{webhook_endpoint_id}", request_options=request_options
        )
        return WebhookEndpoint.deserialize(raw)

    def rotate_secret(
        self,
        webhook_endpoint_id: str,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> WebhookSecretRotation:
        raw = self._http.request(
            "POST",
            f"/webhooks/endpoints/{webhook_endpoint_id}/rotate-secret",
            body=params,
            request_options=request_options,
        )
        return WebhookSecretRotation.deserialize(raw)

    def update(
        self,
        webhook_endpoint_id: str,
        params: UpdateWebhookEndpointRequest,
        request_options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        raw = self._http.request(
            "PATCH",
            f"/webhooks/endpoints/{webhook_endpoint_id}",
            body=UpdateWebhookEndpointRequest.serialize_update(params),
            request_options=request_options,
        )
        return WebhookEndpoint.deserialize(raw)
