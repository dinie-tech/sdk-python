# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class CustomerBankAccountRequest:
    bank_id: str
    branch: str
    digit: str
    kind: Literal["checking", "saving", "payment"]
    number: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerBankAccountRequest:
        return cls(
            bank_id=raw["bank_id"],
            branch=raw["branch"],
            digit=raw["digit"],
            kind=raw["kind"],
            number=raw["number"],
        )

    @staticmethod
    def serialize_upsert_bank_account(params: CustomerBankAccountRequest) -> dict[str, Any]:
        return {
            "bank_account": {
                "bank_id": params.bank_id,
                "branch": params.branch,
                "digit": params.digit,
                "kind": params.kind,
                "number": params.number,
            }
        }
