# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class KycUploadRg:
    attachment_type: Literal["front", "back"]
    evidence_type: Literal["rg"]
    file: str
    requirement_id: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycUploadRg:
        return cls(
            attachment_type=raw["attachment_type"],
            evidence_type=raw["evidence_type"],
            file=raw["file"],
            requirement_id=raw["requirement_id"],
        )
