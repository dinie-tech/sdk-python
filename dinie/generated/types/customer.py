# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import CustomerId
from .kyc_requirement_union import KycRequirement, deserialize_kyc_requirement


@dataclass(frozen=True, slots=True)
class Customer:
    cnpj: str
    cpf: str
    created_at: int
    email: str
    external_id: str
    id: CustomerId
    name: str
    phone: str
    status: Literal["creating", "pending_kyc", "under_review", "active", "denied"]
    trading_name: str
    updated_at: int
    kyc: list[KycRequirement] | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Customer:
        return cls(
            cnpj=raw["cnpj"],
            cpf=raw["cpf"],
            created_at=raw["created_at"],
            email=raw["email"],
            external_id=raw["external_id"],
            id=raw["id"],
            kyc=[deserialize_kyc_requirement(x) for x in raw["kyc"]] if "kyc" in raw else None,
            name=raw["name"],
            phone=raw["phone"],
            status=raw["status"],
            trading_name=raw["trading_name"],
            updated_at=raw["updated_at"],
        )
