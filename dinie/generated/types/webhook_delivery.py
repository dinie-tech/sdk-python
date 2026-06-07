# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import WebhookDeliveryId


@dataclass(frozen=True, slots=True)
class WebhookDelivery:
    attempt_count: int
    created_at: str
    event_type: str
    id: WebhookDeliveryId
    status: Literal["pending", "delivered", "failed"]
    delivered_at: str | None = None
    failed_at: str | None = None
    response_status: int | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> WebhookDelivery:
        return cls(
            attempt_count=raw["attempt_count"],
            created_at=raw["created_at"],
            delivered_at=raw.get("delivered_at"),
            event_type=raw["event_type"],
            failed_at=raw.get("failed_at"),
            id=raw["id"],
            response_status=raw.get("response_status"),
            status=raw["status"],
        )
