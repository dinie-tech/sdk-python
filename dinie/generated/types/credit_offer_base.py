# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import CreditOfferId, CustomerId


@dataclass(frozen=True, slots=True)
class CreditOfferBase:
    approved_amount: float
    created_at: int
    customer_id: CustomerId
    id: CreditOfferId
    min_amount: float
    monthly_interest_rate: float
    status: Literal["available", "accepted", "expired"]
    updated_at: int
    valid_until: int
    due_date_rule: str | None = None
    external_id: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreditOfferBase:
        return cls(
            approved_amount=raw["approved_amount"],
            created_at=raw["created_at"],
            customer_id=raw["customer_id"],
            due_date_rule=raw.get("due_date_rule"),
            external_id=raw.get("external_id"),
            id=raw["id"],
            min_amount=raw["min_amount"],
            monthly_interest_rate=raw["monthly_interest_rate"],
            status=raw["status"],
            updated_at=raw["updated_at"],
            valid_until=raw["valid_until"],
        )
