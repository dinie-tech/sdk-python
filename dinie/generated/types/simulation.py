# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ids import CreditOfferId, SimulationId


@dataclass(frozen=True, slots=True)
class Simulation:
    annual_cet_rate: float
    annual_interest_rate: float
    created_at: int
    credit_offer_id: CreditOfferId
    fee_amount: float
    first_due_date: str
    id: SimulationId
    installment_amount: float
    installment_count: int
    interest_amount: float
    iof_amount: float
    monthly_cet_rate: float
    monthly_interest_rate: float
    principal_amount: float
    requested_amount: float
    total_amount: float

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Simulation:
        return cls(
            annual_cet_rate=raw["annual_cet_rate"],
            annual_interest_rate=raw["annual_interest_rate"],
            created_at=raw["created_at"],
            credit_offer_id=raw["credit_offer_id"],
            fee_amount=raw["fee_amount"],
            first_due_date=raw["first_due_date"],
            id=raw["id"],
            installment_amount=raw["installment_amount"],
            installment_count=raw["installment_count"],
            interest_amount=raw["interest_amount"],
            iof_amount=raw["iof_amount"],
            monthly_cet_rate=raw["monthly_cet_rate"],
            monthly_interest_rate=raw["monthly_interest_rate"],
            principal_amount=raw["principal_amount"],
            requested_amount=raw["requested_amount"],
            total_amount=raw["total_amount"],
        )
