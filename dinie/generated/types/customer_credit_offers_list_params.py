# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class CustomerCreditOffersListParams:
    limit: int | None = None
    starting_after: str | None = None
    status: Literal["available", "accepted", "expired"] | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerCreditOffersListParams:
        return cls(
            limit=raw.get("limit"),
            starting_after=raw.get("starting_after"),
            status=raw.get("status"),
        )
