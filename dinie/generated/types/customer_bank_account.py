# generated — do not edit
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any

from .customer_bank_account_request import CustomerBankAccountRequest
from .ids import BankAccountId


@dataclass(frozen=True, slots=True)
class CustomerBankAccount(CustomerBankAccountRequest):
    _: KW_ONLY
    bank_name: str
    id: BankAccountId
    updated_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerBankAccount:
        return cls(
            bank_id=raw["bank_id"],
            bank_name=raw["bank_name"],
            branch=raw["branch"],
            digit=raw["digit"],
            id=raw["id"],
            kind=raw["kind"],
            number=raw["number"],
            updated_at=raw["updated_at"],
        )
