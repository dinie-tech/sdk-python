# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import CreditOfferId, CustomerId


@dataclass(frozen=True, slots=True)
class CreditOfferData:
    approved_amount: float
    customer_id: CustomerId
    external_id: str
    id: CreditOfferId
    installments: int
    min_amount: float
    monthly_interest_rate: float
    status: Literal["available", "expired"]
    valid_until: int
    due_date_rule: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreditOfferData:
        return cls(
            approved_amount=raw["approved_amount"],
            customer_id=raw["customer_id"],
            external_id=raw["external_id"],
            id=raw["id"],
            installments=raw["installments"],
            min_amount=raw["min_amount"],
            monthly_interest_rate=raw["monthly_interest_rate"],
            status=raw["status"],
            valid_until=raw["valid_until"],
            due_date_rule=raw.get("due_date_rule"),
        )


@dataclass(frozen=True, slots=True)
class CreditOfferAvailable(WebhookEventBase):
    data: CreditOfferData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreditOfferAvailable:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "credit_offer.available"),
            data=CreditOfferData.deserialize(raw.get("data", {})),
        )


__all__ = ["CreditOfferAvailable", "CreditOfferData"]
