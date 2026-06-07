# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ids import EventId


@dataclass(frozen=True, slots=True)
class WebhookEventBase:
    api_version: str
    created_at: int
    delivery_id: str
    id: EventId
    timestamp: int
    type: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> WebhookEventBase:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw["type"],
        )
