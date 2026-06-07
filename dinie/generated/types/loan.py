# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import CreditOfferId, CustomerId, LoanId, SimulationId


@dataclass(frozen=True, slots=True)
class Loan:
    annual_cet_rate: float
    annual_interest_rate: float
    ccb_number: str
    created_at: int
    credit_offer_id: CreditOfferId
    customer_id: CustomerId
    disbursement_method: str
    first_due_date: str
    id: LoanId
    installment_amount: float
    installment_count: int
    iof_amount: float
    monthly_cet_rate: float
    monthly_interest_rate: float
    principal_amount: float
    requested_amount: float
    signing_url: str
    simulation_id: SimulationId
    status: Literal["awaiting_signatures", "processing", "active", "finished", "cancelled", "error"]
    total_amount: float
    updated_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Loan:
        return cls(
            annual_cet_rate=raw["annual_cet_rate"],
            annual_interest_rate=raw["annual_interest_rate"],
            ccb_number=raw["ccb_number"],
            created_at=raw["created_at"],
            credit_offer_id=raw["credit_offer_id"],
            customer_id=raw["customer_id"],
            disbursement_method=raw["disbursement_method"],
            first_due_date=raw["first_due_date"],
            id=raw["id"],
            installment_amount=raw["installment_amount"],
            installment_count=raw["installment_count"],
            iof_amount=raw["iof_amount"],
            monthly_cet_rate=raw["monthly_cet_rate"],
            monthly_interest_rate=raw["monthly_interest_rate"],
            principal_amount=raw["principal_amount"],
            requested_amount=raw["requested_amount"],
            signing_url=raw["signing_url"],
            simulation_id=raw["simulation_id"],
            status=raw["status"],
            total_amount=raw["total_amount"],
            updated_at=raw["updated_at"],
        )
