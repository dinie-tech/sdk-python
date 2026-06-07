# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .income_statement_submitted import IncomeStatementSubmitted


@dataclass(frozen=True, slots=True)
class IncomeStatementRequirement:
    label: str
    mandatory: bool
    requirement_id: Literal["income_statement"]
    requirement_type: Literal["income_statement"]
    submitted: IncomeStatementSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IncomeStatementRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            submitted=IncomeStatementSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
