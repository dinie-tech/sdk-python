"""Dinie Python SDK.

Official SDK for the Dinie V3 API. Import the client and call it:

    import dinie
    client = dinie.Dinie(client_id="...", client_secret="...")

Webhook events:

    from dinie.webhooks import extract
    event = extract(payload, headers)
    match event:
        case dinie.CustomerCreatedEvent(): ...
"""

from __future__ import annotations

import importlib.metadata

from dinie.generated.client import Dinie
from dinie.generated.events import WebhookEvent
from dinie.generated.events.credit_offer_available import CreditOfferAvailable
from dinie.generated.events.credit_offer_expired import CreditOfferExpired
from dinie.generated.events.customer_active import CustomerActive
from dinie.generated.events.customer_created import CustomerCreated
from dinie.generated.events.customer_denied import CustomerDenied
from dinie.generated.events.customer_kyc_updated import CustomerKycUpdated
from dinie.generated.events.customer_under_review import CustomerUnderReview
from dinie.generated.events.loan_active import LoanActive
from dinie.generated.events.loan_cancelled import LoanCancelled
from dinie.generated.events.loan_created import LoanCreated
from dinie.generated.events.loan_error import LoanError
from dinie.generated.events.loan_finished import LoanFinished
from dinie.generated.events.loan_payment_received import LoanPaymentReceived
from dinie.generated.events.loan_processing import LoanProcessing
from dinie.generated.events.loan_signature_received import LoanSignatureReceived
from dinie.runtime.errors import (
    APIConnectionError,
    ApiError,
    APITimeoutError,
    SessionTokenExpiredError,
)

try:
    __version__: str = importlib.metadata.version("dinie-sdk")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0+dev"

# C-COLO-2: __version__ is derived from the installed package metadata (PEP 566).
# sdk_version in the User-Agent (runtime/http.py) reads from the same source via
# importlib.metadata.version("dinie-sdk") so both track the manifest, not a second literal.

__all__ = [
    "__version__",
    "Dinie",
    "WebhookEvent",
    # Event types (for match/case and isinstance checks)
    "CreditOfferAvailable",
    "CreditOfferExpired",
    "CustomerActive",
    "CustomerCreated",
    "CustomerDenied",
    "CustomerKycUpdated",
    "CustomerUnderReview",
    "LoanActive",
    "LoanCancelled",
    "LoanCreated",
    "LoanError",
    "LoanFinished",
    "LoanPaymentReceived",
    "LoanProcessing",
    "LoanSignatureReceived",
    # Errors
    "ApiError",
    "APIConnectionError",
    "APITimeoutError",
    "SessionTokenExpiredError",
]
