# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LoanPayment:
    amount: float
    installment_number: int
    paid_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanPayment:
        return cls(
            amount=raw["amount"],
            installment_number=raw["installment_number"],
            paid_at=raw["paid_at"],
        )
