# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ids import ApiClientId


@dataclass(frozen=True, slots=True)
class Credential:
    client_id: ApiClientId
    created_at: int
    expires_at: int
    id: ApiClientId
    last_used_at: int
    name: str
    status: Literal["active", "revoked"]
    updated_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Credential:
        return cls(
            client_id=raw["client_id"],
            created_at=raw["created_at"],
            expires_at=raw["expires_at"],
            id=raw["id"],
            last_used_at=raw["last_used_at"],
            name=raw["name"],
            status=raw["status"],
            updated_at=raw["updated_at"],
        )
