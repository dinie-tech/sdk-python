# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import LoanId, TransactionId


@dataclass(frozen=True, slots=True)
class Transaction:
    amount_due: float
    amount_paid: float
    amount_remaining: float
    created_at: int
    days_overdue: int
    due_date: str
    fees: float
    id: TransactionId
    interest: float
    loan_id: LoanId
    paid_at: int
    principal: float
    status: Literal["pending", "paid", "overdue", "partially_paid"]
    type: Literal["installment"]
    updated_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Transaction:
        return cls(
            amount_due=raw["amount_due"],
            amount_paid=raw["amount_paid"],
            amount_remaining=raw["amount_remaining"],
            created_at=raw["created_at"],
            days_overdue=raw["days_overdue"],
            due_date=raw["due_date"],
            fees=raw["fees"],
            id=raw["id"],
            interest=raw["interest"],
            loan_id=raw["loan_id"],
            paid_at=raw["paid_at"],
            principal=raw["principal"],
            status=raw["status"],
            type=raw["type"],
            updated_at=raw["updated_at"],
        )
