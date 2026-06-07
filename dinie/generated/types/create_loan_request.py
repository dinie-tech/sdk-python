# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ids import CreditOfferId, SimulationId


@dataclass(frozen=True, slots=True)
class CreateLoanRequest:
    credit_offer_id: CreditOfferId
    first_due_date: str
    installment_amount: float
    installment_count: int
    simulation_id: SimulationId

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreateLoanRequest:
        return cls(
            credit_offer_id=raw["credit_offer_id"],
            first_due_date=raw["first_due_date"],
            installment_amount=raw["installment_amount"],
            installment_count=raw["installment_count"],
            simulation_id=raw["simulation_id"],
        )

    @staticmethod
    def serialize_create(params: CreateLoanRequest) -> dict[str, Any]:
        return {
            "credit_offer_id": params.credit_offer_id,
            "first_due_date": params.first_due_date,
            "installment_amount": params.installment_amount,
            "installment_count": params.installment_count,
            "simulation_id": params.simulation_id,
        }
