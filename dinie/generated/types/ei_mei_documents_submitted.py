# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .ei_mei_documents_attachment import EiMeiDocumentsAttachment
from .enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class EiMeiDocumentsSubmitted:
    attachments: list[EiMeiDocumentsAttachment]
    evidence_type: Literal["ei_mei"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EiMeiDocumentsSubmitted:
        return cls(
            attachments=[EiMeiDocumentsAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
