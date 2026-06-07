# generated — do not edit
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any

from .credential import Credential


@dataclass(frozen=True, slots=True)
class CredentialWithSecret(Credential):
    _: KW_ONLY
    client_secret: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CredentialWithSecret:
        return cls(
            client_id=raw["client_id"],
            client_secret=raw["client_secret"],
            created_at=raw["created_at"],
            expires_at=raw["expires_at"],
            id=raw["id"],
            last_used_at=raw["last_used_at"],
            name=raw["name"],
            status=raw["status"],
            updated_at=raw["updated_at"],
        )
