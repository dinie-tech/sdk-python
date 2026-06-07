# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .company_document_submitted import CompanyDocumentSubmitted


@dataclass(frozen=True, slots=True)
class CompanyDocumentRequirement:
    label: str
    mandatory: bool
    requirement_id: str
    requirement_type: Literal["company_document"]
    submitted: CompanyDocumentSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CompanyDocumentRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            submitted=CompanyDocumentSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
