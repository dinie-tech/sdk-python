# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .eireli_incorporation_statement_submitted import EireliIncorporationStatementSubmitted


@dataclass(frozen=True, slots=True)
class EireliIncorporationStatementRequirement:
    label: str
    mandatory: bool
    requirement_id: Literal["eireli_incorporation_statement"]
    requirement_type: Literal["eireli_incorporation_statement"]
    submitted: EireliIncorporationStatementSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EireliIncorporationStatementRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            submitted=EireliIncorporationStatementSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
