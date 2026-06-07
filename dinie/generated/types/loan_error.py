# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LoanError:
    code: str
    message: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanError:
        return cls(
            code=raw["code"],
            message=raw["message"],
        )
