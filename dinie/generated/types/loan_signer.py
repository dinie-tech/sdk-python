# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LoanSigner:
    cpf: str
    name: str
    signed_at: int

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanSigner:
        return cls(
            cpf=raw["cpf"],
            name=raw["name"],
            signed_at=raw["signed_at"],
        )
