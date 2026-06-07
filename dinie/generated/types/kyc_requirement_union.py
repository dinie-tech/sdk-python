# generated — do not edit
from __future__ import annotations

from typing import Any

from .articles_of_association_requirement import ArticlesOfAssociationRequirement
from .company_document_requirement import CompanyDocumentRequirement
from .ei_mei_documents_requirement import EiMeiDocumentsRequirement
from .eireli_incorporation_statement_requirement import EireliIncorporationStatementRequirement
from .email_requirement import EmailRequirement
from .identity_requirement import IdentityRequirement
from .income_statement_requirement import IncomeStatementRequirement
from .proof_of_address_requirement import ProofOfAddressRequirement
from .selfie_requirement import SelfieRequirement

KycRequirement = (
    ArticlesOfAssociationRequirement
    | CompanyDocumentRequirement
    | EiMeiDocumentsRequirement
    | EireliIncorporationStatementRequirement
    | EmailRequirement
    | IdentityRequirement
    | IncomeStatementRequirement
    | ProofOfAddressRequirement
    | SelfieRequirement
)


def deserialize_kyc_requirement(raw: dict[str, Any]) -> KycRequirement:
    """Dispatch on the `requirement_type` field value."""
    _disc = raw.get("requirement_type")
    match _disc:
        case "identity":
            return IdentityRequirement.deserialize(raw)
        case "selfie":
            return SelfieRequirement.deserialize(raw)
        case "proof_of_address":
            return ProofOfAddressRequirement.deserialize(raw)
        case "company_document":
            return CompanyDocumentRequirement.deserialize(raw)
        case "ei_mei_documents":
            return EiMeiDocumentsRequirement.deserialize(raw)
        case "income_statement":
            return IncomeStatementRequirement.deserialize(raw)
        case "articles_of_association":
            return ArticlesOfAssociationRequirement.deserialize(raw)
        case "eireli_incorporation_statement":
            return EireliIncorporationStatementRequirement.deserialize(raw)
        case "email":
            return EmailRequirement.deserialize(raw)

        case _:
            raise ValueError(f"Unknown KycRequirement discriminator value: {_disc!r}")


__all__ = ["KycRequirement", "deserialize_kyc_requirement"]
