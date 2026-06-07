# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import CustomerId


@dataclass(frozen=True, slots=True)
class CustomerStatusData:
    external_id: str
    id: CustomerId
    status: Literal["under_review", "active"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerStatusData:
        return cls(
            external_id=raw["external_id"],
            id=raw["id"],
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class CustomerUnderReview(WebhookEventBase):
    data: CustomerStatusData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerUnderReview:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "customer.under_review"),
            data=CustomerStatusData.deserialize(raw.get("data", {})),
        )


__all__ = ["CustomerUnderReview", "CustomerStatusData"]
