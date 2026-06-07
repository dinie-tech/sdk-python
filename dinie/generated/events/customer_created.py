# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import KycRequirement, WebhookEventBase, deserialize_kyc_requirement
from ..types.ids import CustomerId


@dataclass(frozen=True, slots=True)
class CustomerCreatedData:
    cpf: str
    email: str
    external_id: str
    id: CustomerId
    kyc: list[KycRequirement]
    name: str
    phone: str
    status: Literal["pending_kyc"]
    trading_name: str
    cnpj: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerCreatedData:
        return cls(
            cpf=raw["cpf"],
            email=raw["email"],
            external_id=raw["external_id"],
            id=raw["id"],
            kyc=[deserialize_kyc_requirement(x) for x in raw["kyc"]],
            name=raw["name"],
            phone=raw["phone"],
            status=raw["status"],
            trading_name=raw["trading_name"],
            cnpj=raw.get("cnpj"),
        )


@dataclass(frozen=True, slots=True)
class CustomerCreated(WebhookEventBase):
    data: CustomerCreatedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerCreated:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "customer.created"),
            data=CustomerCreatedData.deserialize(raw.get("data", {})),
        )


__all__ = ["CustomerCreated", "CustomerCreatedData"]
