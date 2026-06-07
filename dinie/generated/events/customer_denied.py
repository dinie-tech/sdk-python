# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import CustomerId


@dataclass(frozen=True, slots=True)
class CustomerDeniedData:
    cpf: str
    email: str
    external_id: str
    id: CustomerId
    name: str
    phone: str
    status: Literal["denied"]
    cnpj: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerDeniedData:
        return cls(
            cpf=raw["cpf"],
            email=raw["email"],
            external_id=raw["external_id"],
            id=raw["id"],
            name=raw["name"],
            phone=raw["phone"],
            status=raw["status"],
            cnpj=raw.get("cnpj"),
        )


@dataclass(frozen=True, slots=True)
class CustomerDenied(WebhookEventBase):
    data: CustomerDeniedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerDenied:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "customer.denied"),
            data=CustomerDeniedData.deserialize(raw.get("data", {})),
        )


__all__ = ["CustomerDenied", "CustomerDeniedData"]
