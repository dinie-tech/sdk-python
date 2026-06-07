# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class CustomersListParams:
    cpf: str | None = None
    external_id: str | None = None
    limit: int | None = None
    order: Literal["asc", "desc"] | None = None
    sort: Literal["created_at", "updated_at"] | None = None
    starting_after: str | None = None
    status: Literal["creating", "pending_kyc", "under_review", "active", "denied"] | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomersListParams:
        return cls(
            cpf=raw.get("cpf"),
            external_id=raw.get("external_id"),
            limit=raw.get("limit"),
            order=raw.get("order"),
            sort=raw.get("sort"),
            starting_after=raw.get("starting_after"),
            status=raw.get("status"),
        )
