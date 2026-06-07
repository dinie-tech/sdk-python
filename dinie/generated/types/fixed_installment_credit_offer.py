# generated — do not edit
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any

from .credit_offer_base import CreditOfferBase


@dataclass(frozen=True, slots=True)
class FixedInstallmentCreditOffer(CreditOfferBase):
    _: KW_ONLY
    installments: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> FixedInstallmentCreditOffer:
        return cls(
            approved_amount=raw["approved_amount"],
            created_at=raw["created_at"],
            customer_id=raw["customer_id"],
            due_date_rule=raw.get("due_date_rule"),
            external_id=raw.get("external_id"),
            id=raw["id"],
            installments=raw["installments"],
            min_amount=raw["min_amount"],
            monthly_interest_rate=raw["monthly_interest_rate"],
            status=raw["status"],
            updated_at=raw["updated_at"],
            valid_until=raw["valid_until"],
        )
