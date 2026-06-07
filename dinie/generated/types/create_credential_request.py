# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateCredentialRequest:
    name: str
    expires_at: int | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreateCredentialRequest:
        return cls(
            expires_at=raw.get("expires_at"),
            name=raw["name"],
        )

    @staticmethod
    def serialize_create(params: CreateCredentialRequest) -> dict[str, Any]:
        out: dict[str, Any] = {"name": params.name}
        if params.expires_at is not None:
            out["expires_at"] = params.expires_at
        return out
