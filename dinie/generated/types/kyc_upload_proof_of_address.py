# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class KycUploadProofOfAddress:
    attachment_type: Literal["file"]
    evidence_type: Literal["proof_of_address"]
    file: str
    requirement_id: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycUploadProofOfAddress:
        return cls(
            attachment_type=raw["attachment_type"],
            evidence_type=raw["evidence_type"],
            file=raw["file"],
            requirement_id=raw["requirement_id"],
        )
