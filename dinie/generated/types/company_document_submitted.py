# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .company_document_attachment import CompanyDocumentAttachment
from .enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class CompanyDocumentSubmitted:
    attachments: list[CompanyDocumentAttachment]
    evidence_type: Literal["ccmei"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CompanyDocumentSubmitted:
        return cls(
            attachments=[CompanyDocumentAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
