# generated — do not edit
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any

from .webhook_endpoint import WebhookEndpoint


@dataclass(frozen=True, slots=True)
class WebhookEndpointWithSecret(WebhookEndpoint):
    _: KW_ONLY
    secret: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> WebhookEndpointWithSecret:
        return cls(
            created_at=raw["created_at"],
            description=raw["description"],
            events=raw["events"],
            id=raw["id"],
            secret=raw["secret"],
            status=raw["status"],
            updated_at=raw["updated_at"],
            url=raw["url"],
        )
