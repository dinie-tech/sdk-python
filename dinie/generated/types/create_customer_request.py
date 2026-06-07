# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateCustomerRequest:
    cnpj: str
    cpf: str
    email: str
    phone: str
    external_id: str | None = None
    name: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreateCustomerRequest:
        return cls(
            cnpj=raw["cnpj"],
            cpf=raw["cpf"],
            email=raw["email"],
            external_id=raw.get("external_id"),
            name=raw.get("name"),
            phone=raw["phone"],
        )

    @staticmethod
    def serialize_create(params: CreateCustomerRequest) -> dict[str, Any]:
        out: dict[str, Any] = {
            "cnpj": params.cnpj,
            "cpf": params.cpf,
            "email": params.email,
            "phone": params.phone,
        }
        if params.external_id is not None:
            out["external_id"] = params.external_id
        if params.name is not None:
            out["name"] = params.name
        return out
