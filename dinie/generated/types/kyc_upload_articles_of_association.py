# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class KycUploadArticlesOfAssociation:
    attachment_type: Literal["file"]
    evidence_type: Literal["articles_of_association"]
    file: str
    requirement_id: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycUploadArticlesOfAssociation:
        return cls(
            attachment_type=raw["attachment_type"],
            evidence_type=raw["evidence_type"],
            file=raw["file"],
            requirement_id=raw["requirement_id"],
        )
