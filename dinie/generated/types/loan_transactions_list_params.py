# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LoanTransactionsListParams:
    limit: int | None = None
    starting_after: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanTransactionsListParams:
        return cls(
            limit=raw.get("limit"),
            starting_after=raw.get("starting_after"),
        )
