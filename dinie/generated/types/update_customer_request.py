# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class UpdateCustomerRequest:
    email: str | None = None
    phone: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> UpdateCustomerRequest:
        return cls(
            email=raw.get("email"),
            phone=raw.get("phone"),
        )

    @staticmethod
    def serialize_update(params: UpdateCustomerRequest) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if params.email is not None:
            out["email"] = params.email
        if params.phone is not None:
            out["phone"] = params.phone
        return out
