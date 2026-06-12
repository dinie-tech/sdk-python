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
    """WebhookEndpoints resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        params: CreateWebhookEndpointRequest,
        request_options: RequestOptions | None = None,
    ) -> WebhookEndpointWithSecret:
        """
        Create a webhook endpoint

        Create a webhook endpoint; the HMAC signing `secret` is returned only in this response

        :param params: Request parameters.
        """
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
        """
        Delete a webhook endpoint

        Delete a webhook endpoint and stop all deliveries

        :param webhook_endpoint_id: Identificador único do endpoint de webhook
        """
        self._http.request(
            "DELETE", f"/webhooks/endpoints/{webhook_endpoint_id}", request_options=request_options
        )

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookEndpoint]:
        """
        List webhook endpoints

        List all configured webhook endpoints with URL, subscribed events, and status
        """
        raw = self._http.request("GET", "/webhooks/endpoints", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=WebhookEndpoint.deserialize)

    def retrieve(
        self,
        webhook_endpoint_id: str,
        request_options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """
        Retrieve a webhook endpoint

        Return details of a specific webhook endpoint including URL, events, and status

        :param webhook_endpoint_id: Identificador único do endpoint de webhook
        """
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
        """
        Rotate the signing secret

        Rotate the HMAC signing secret; the previous secret remains valid for the grace period

        :param webhook_endpoint_id: Identificador único do endpoint de webhook
        :param params: Request parameters.
        """
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
        """
        Update a webhook endpoint

        Update URL, events, description, or status of a webhook endpoint

        :param webhook_endpoint_id: Identificador único do endpoint de webhook
        :param params: Request parameters.
        """
        raw = self._http.request(
            "PATCH",
            f"/webhooks/endpoints/{webhook_endpoint_id}",
            body=UpdateWebhookEndpointRequest.serialize_update(params),
            request_options=request_options,
        )
        return WebhookEndpoint.deserialize(raw)
