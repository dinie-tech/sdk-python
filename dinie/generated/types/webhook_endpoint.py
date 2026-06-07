# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import WebhookEndpointId


@dataclass(frozen=True, slots=True)
class WebhookEndpoint:
    created_at: int
    description: str
    events: list[Any]
    id: WebhookEndpointId
    status: Literal["active", "disabled"]
    updated_at: int
    url: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> WebhookEndpoint:
        return cls(
            created_at=raw["created_at"],
            description=raw["description"],
            events=raw["events"],
            id=raw["id"],
            status=raw["status"],
            updated_at=raw["updated_at"],
            url=raw["url"],
        )
