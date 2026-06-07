# generated — do not edit
from __future__ import annotations

import re
from typing import NewType

ApiClientId = NewType("ApiClientId", str)
API_CLIENT_ID_PATTERN = re.compile(r"^dinie_ci_(live|test)_[A-Za-z0-9]+$")

BankAccountId = NewType("BankAccountId", str)
BANK_ACCOUNT_ID_PATTERN = re.compile(r"^ba_[0-9a-f]{32}$")

CreditOfferId = NewType("CreditOfferId", str)
CREDIT_OFFER_ID_PATTERN = re.compile(r"^co_[0-9a-f]{32}$")

CustomerId = NewType("CustomerId", str)
CUSTOMER_ID_PATTERN = re.compile(r"^cust_[0-9a-f]{32}$")

EventId = NewType("EventId", str)
EVENT_ID_PATTERN = re.compile(r"^evt_[0-9a-f]{32}$")

LoanId = NewType("LoanId", str)
LOAN_ID_PATTERN = re.compile(r"^ln_[0-9a-f]{32}$")

SimulationId = NewType("SimulationId", str)
SIMULATION_ID_PATTERN = re.compile(r"^sim_[0-9a-f]{32}$")

TransactionId = NewType("TransactionId", str)
TRANSACTION_ID_PATTERN = re.compile(r"^tx_[0-9a-f]{32}$")

WebhookDeliveryId = NewType("WebhookDeliveryId", str)
WEBHOOK_DELIVERY_ID_PATTERN = re.compile(r"^dlv_[0-9a-f]{32}$")

WebhookEndpointId = NewType("WebhookEndpointId", str)
WEBHOOK_ENDPOINT_ID_PATTERN = re.compile(r"^we_[0-9a-f]{32}$")


__all__ = [
    "ApiClientId",
    "API_CLIENT_ID_PATTERN",
    "BankAccountId",
    "BANK_ACCOUNT_ID_PATTERN",
    "CreditOfferId",
    "CREDIT_OFFER_ID_PATTERN",
    "CustomerId",
    "CUSTOMER_ID_PATTERN",
    "EventId",
    "EVENT_ID_PATTERN",
    "LoanId",
    "LOAN_ID_PATTERN",
    "SimulationId",
    "SIMULATION_ID_PATTERN",
    "TransactionId",
    "TRANSACTION_ID_PATTERN",
    "WebhookDeliveryId",
    "WEBHOOK_DELIVERY_ID_PATTERN",
    "WebhookEndpointId",
    "WEBHOOK_ENDPOINT_ID_PATTERN",
]
