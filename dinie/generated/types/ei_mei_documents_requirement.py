# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ei_mei_documents_submitted import EiMeiDocumentsSubmitted


@dataclass(frozen=True, slots=True)
class EiMeiDocumentsRequirement:
    label: str
    mandatory: bool
    requirement_id: Literal["ei_mei_documents"]
    requirement_type: Literal["ei_mei_documents"]
    submitted: EiMeiDocumentsSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EiMeiDocumentsRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            submitted=EiMeiDocumentsSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
