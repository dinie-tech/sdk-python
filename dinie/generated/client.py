# generated — do not edit
from __future__ import annotations

import httpx

from ..runtime.http import SyncHttpClient
from ..runtime.token_manager import TokenManager
from .resources.banks import Banks
from .resources.biometrics import Biometrics
from .resources.credentials import Credentials
from .resources.credit_offers import CreditOffers
from .resources.customers import Customers
from .resources.loans import Loans
from .resources.webhook_endpoints import WebhookEndpoints

DEFAULT_BASE_URL = "https://api.dinie.com.br/api/v3"


class Dinie:
    """Dinie SDK client — sync, httpx-based. OAuth2 token management is transparent."""

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        code: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        idempotency: bool = True,
        http_client: httpx.Client | None = None,
        _shared_http: SyncHttpClient | None = None,
    ) -> None:
        if _shared_http is not None:
            # with_options() clone path: reuse existing SyncHttpClient.
            # Shares the same TokenManager and httpx pool — no extra token POST (D10).
            self._options = {
                "base_url": _shared_http._base_url,
                "timeout": _shared_http._default_timeout,
                "max_retries": _shared_http._default_max_retries,
                "idempotency": idempotency,
            }
            self._token_manager = _shared_http._token_manager
            self._http = _shared_http
        else:
            import os

            resolved_id = client_id or os.environ.get("DINIE_CLIENT_ID")
            resolved_secret = client_secret or os.environ.get("DINIE_CLIENT_SECRET")
            resolved_base = base_url or os.environ.get("DINIE_BASE_URL") or DEFAULT_BASE_URL

            if not resolved_id:
                raise ValueError("Missing Dinie client_id: pass client_id= or set DINIE_CLIENT_ID.")
            if not resolved_secret:
                raise ValueError(
                    "Missing Dinie client_secret: pass client_secret= or set DINIE_CLIENT_SECRET."
                )

            self._options = {
                "timeout": timeout,
                "max_retries": max_retries,
                "idempotency": idempotency,
                "base_url": resolved_base,
            }

            _http_client = http_client or httpx.Client(base_url=resolved_base, timeout=timeout)
            self._token_manager = TokenManager(
                client_id=resolved_id,
                client_secret=resolved_secret,
                base_url=resolved_base,
                http_client=_http_client,
                code=code,
            )
            self._http = SyncHttpClient(
                token_manager=self._token_manager,
                http_client=_http_client,
                base_url=resolved_base,
                max_retries=max_retries,
                timeout=timeout,
            )
        self.banks = Banks(self._http)
        self.biometrics = Biometrics(self._http)
        self.credentials = Credentials(self._http)
        self.credit_offers = CreditOffers(self._http)
        self.customers = Customers(self._http)
        self.loans = Loans(self._http)
        self.webhook_endpoints = WebhookEndpoints(self._http)

    def with_options(self, **overrides: object) -> Dinie:
        """Return a clone sharing the same TokenManager and httpx pool (D10 — no extra token POST).

        Delegates to ``SyncHttpClient.with_options()`` so the underlying transport is correctly
        shared. Only ``base_url``, ``timeout``, ``max_retries``, and ``idempotency`` are
        configurable here; per-call overrides belong in ``RequestOptions``.
        """
        opts: dict[str, object] = {**self._options, **overrides}
        new_http = self._http.with_options(
            base_url=str(opts.get("base_url") or self._options["base_url"]),
            max_retries=int(str(opts.get("max_retries") or self._options["max_retries"])),
            timeout=float(str(opts.get("timeout") or self._options["timeout"])),
        )
        return self.__class__(
            _shared_http=new_http,
            idempotency=bool(
                opts.get("idempotency") if "idempotency" in opts else self._options["idempotency"]
            ),
        )
