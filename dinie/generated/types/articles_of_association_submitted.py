# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .articles_of_association_attachment import ArticlesOfAssociationAttachment
from .enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class ArticlesOfAssociationSubmitted:
    attachments: list[ArticlesOfAssociationAttachment]
    evidence_type: Literal["articles_of_association"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> ArticlesOfAssociationSubmitted:
        return cls(
            attachments=[
                ArticlesOfAssociationAttachment.deserialize(x) for x in raw["attachments"]
            ],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
