# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .articles_of_association_submitted import ArticlesOfAssociationSubmitted


@dataclass(frozen=True, slots=True)
class ArticlesOfAssociationRequirement:
    label: str
    mandatory: bool
    requirement_id: Literal["articles_of_association"]
    requirement_type: Literal["articles_of_association"]
    submitted: ArticlesOfAssociationSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> ArticlesOfAssociationRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            submitted=ArticlesOfAssociationSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
