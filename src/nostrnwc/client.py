"""NWC client — connect to a wallet service and send NIP-47 requests."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

import websockets

from nostrkey.events import UnsignedEvent, sign_event, NostrEvent
from nostrkey.crypto import encrypt, decrypt
from nostrkey.keys import private_key_to_public_key

from nostrnwc.connection import NWCConnection
from nostrnwc.types import (
    BalanceResponse,
    GetInfoResponse,
    ListTransactionsResponse,
    LookupInvoiceResponse,
    MakeInvoiceResponse,
    NWCError,
    PayResponse,
    Transaction,
)

# NIP-47 event kinds
NWC_REQUEST_KIND = 23194
NWC_RESPONSE_KIND = 23195
NWC_INFO_KIND = 13194

# Default timeout for waiting on wallet responses (seconds)
DEFAULT_TIMEOUT = 30


class NWCClient:
    """Async client for Nostr Wallet Connect (NIP-47).

    Connects to a wallet service via a relay and sends encrypted payment
    requests. All communication uses NIP-44 encryption over NIP-47 event kinds.

    Usage:
        from nostrnwc import NWCClient

        async with NWCClient("nostr+walletconnect://...") as nwc:
            balance = await nwc.get_balance()
            print(f"Balance: {balance.balance} msats")
    """

    def __init__(self, connection_string: str, timeout: int = DEFAULT_TIMEOUT):
        """Initialize the NWC client.

        Args:
            connection_string: A nostr+walletconnect:// URI from the wallet service.
            timeout: Seconds to wait for wallet responses (default 30).
        """
        self._conn = NWCConnection.parse(connection_string)
        self._timeout = timeout
        self._ws = None
        self._client_pubkey = private_key_to_public_key(self._conn.secret)

    async def __aenter__(self):
        self._ws = await websockets.connect(self._conn.relay)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._ws:
            await self._ws.close()

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        """Send an encrypted NIP-47 request and wait for the response.

        Args:
            method: NIP-47 method name (e.g. "pay_invoice", "get_balance").
            params: Optional method parameters.

        Returns:
            Parsed result dict from the wallet response.

        Raises:
            RuntimeError: If not connected or wallet returns an error.
            TimeoutError: If no response within timeout.
        """
        if not self._ws:
            raise RuntimeError("Not connected — use 'async with NWCClient(uri) as nwc:'")

        # Build the request payload
        request_payload = {"method": method}
        if params:
            request_payload["params"] = params

        # Encrypt the payload with NIP-44
        plaintext = json.dumps(request_payload)
        ciphertext = encrypt(
            sender_nsec=self._conn.secret,  # encrypt accepts hex
            recipient_npub=self._conn.wallet_pubkey,  # encrypt accepts hex
            plaintext=plaintext,
        )

        # Build and sign the NIP-47 request event (kind 23194)
        event = UnsignedEvent(
            kind=NWC_REQUEST_KIND,
            content=ciphertext,
            tags=[["p", self._conn.wallet_pubkey]],
        )
        signed = sign_event(self._conn.secret, event)

        # Subscribe to responses tagged to our request
        sub_id = str(uuid.uuid4())[:8]
        sub_filter = {
            "kinds": [NWC_RESPONSE_KIND],
            "authors": [self._conn.wallet_pubkey],
            "#p": [self._client_pubkey],
            "#e": [signed.id],
            "since": signed.created_at - 1,
        }
        await self._ws.send(json.dumps(["REQ", sub_id, sub_filter]))

        # Publish the request
        await self._ws.send(json.dumps(["EVENT", signed.to_dict()]))

        # Wait for the response
        deadline = time.monotonic() + self._timeout
        try:
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
                data = json.loads(raw)

                if data[0] == "EVENT" and data[1] == sub_id:
                    response_event = data[2]
                    # Decrypt the response content
                    response_plaintext = decrypt(
                        recipient_nsec=self._conn.secret,
                        sender_npub=self._conn.wallet_pubkey,
                        ciphertext=response_event["content"],
                    )
                    result = json.loads(response_plaintext)

                    # Close the subscription
                    await self._ws.send(json.dumps(["CLOSE", sub_id]))

                    # Check for error
                    if "error" in result:
                        err = result["error"]
                        raise NWCError(
                            code=err.get("code", "UNKNOWN"),
                            message=err.get("message", "Unknown wallet error"),
                        )

                    return result.get("result", {})

                elif data[0] == "EOSE" and data[1] == sub_id:
                    # End of stored events — keep waiting for live events
                    continue

        except asyncio.TimeoutError:
            pass

        await self._ws.send(json.dumps(["CLOSE", sub_id]))
        raise TimeoutError(f"No response from wallet within {self._timeout}s for method '{method}'")

    # ── Public API ──────────────────────────────────────────────────

    async def get_info(self) -> GetInfoResponse:
        """Get wallet info and supported methods (get_info)."""
        result = await self._send_request("get_info")
        return GetInfoResponse(
            alias=result.get("alias", ""),
            color=result.get("color", ""),
            pubkey=result.get("pubkey", ""),
            network=result.get("network", ""),
            block_height=result.get("block_height", 0),
            block_hash=result.get("block_hash", ""),
            methods=result.get("methods", []),
        )

    async def get_balance(self) -> BalanceResponse:
        """Check the wallet balance in millisatoshis (get_balance)."""
        result = await self._send_request("get_balance")
        return BalanceResponse(balance=result.get("balance", 0))

    async def pay_invoice(self, invoice: str, amount: int | None = None) -> PayResponse:
        """Pay a Lightning invoice (pay_invoice).

        Args:
            invoice: Bolt11 payment request string.
            amount: Optional amount in millisatoshis (overrides invoice amount for zero-amount invoices).

        Returns:
            PayResponse with the payment preimage.
        """
        params: dict[str, Any] = {"invoice": invoice}
        if amount is not None:
            params["amount"] = amount
        result = await self._send_request("pay_invoice", params)
        return PayResponse(preimage=result.get("preimage", ""))

    async def make_invoice(
        self,
        amount: int,
        description: str = "",
        description_hash: str = "",
        expiry: int | None = None,
    ) -> MakeInvoiceResponse:
        """Create a Lightning invoice (make_invoice).

        Args:
            amount: Amount in millisatoshis.
            description: Human-readable description for the invoice.
            description_hash: SHA-256 hash of the description (for long descriptions).
            expiry: Invoice expiry in seconds.

        Returns:
            MakeInvoiceResponse with invoice string and payment_hash.
        """
        params: dict[str, Any] = {"amount": amount}
        if description:
            params["description"] = description
        if description_hash:
            params["description_hash"] = description_hash
        if expiry is not None:
            params["expiry"] = expiry
        result = await self._send_request("make_invoice", params)
        return MakeInvoiceResponse(
            invoice=result.get("invoice", ""),
            payment_hash=result.get("payment_hash", ""),
        )

    async def lookup_invoice(
        self,
        payment_hash: str = "",
        invoice: str = "",
    ) -> LookupInvoiceResponse:
        """Look up an invoice by payment hash or bolt11 string (lookup_invoice).

        Args:
            payment_hash: Hex-encoded payment hash.
            invoice: Bolt11 payment request string.

        Returns:
            LookupInvoiceResponse with payment status.
        """
        params: dict[str, Any] = {}
        if payment_hash:
            params["payment_hash"] = payment_hash
        if invoice:
            params["invoice"] = invoice
        if not params:
            raise ValueError("Either payment_hash or invoice must be provided")
        result = await self._send_request("lookup_invoice", params)
        return LookupInvoiceResponse(
            invoice=result.get("invoice", ""),
            paid=result.get("paid", False),
            preimage=result.get("preimage"),
        )

    async def list_transactions(
        self,
        from_timestamp: int | None = None,
        until_timestamp: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        unpaid: bool = False,
        type: str | None = None,
    ) -> ListTransactionsResponse:
        """List past transactions (list_transactions).

        Args:
            from_timestamp: Filter transactions after this unix timestamp.
            until_timestamp: Filter transactions before this unix timestamp.
            limit: Maximum number of transactions to return.
            offset: Number of transactions to skip.
            unpaid: Include unpaid transactions.
            type: Filter by "incoming" or "outgoing".

        Returns:
            ListTransactionsResponse with list of Transaction objects.
        """
        params: dict[str, Any] = {}
        if from_timestamp is not None:
            params["from"] = from_timestamp
        if until_timestamp is not None:
            params["until"] = until_timestamp
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if unpaid:
            params["unpaid"] = True
        if type:
            params["type"] = type
        result = await self._send_request("list_transactions", params)

        transactions = []
        for tx in result.get("transactions", []):
            transactions.append(
                Transaction(
                    type=tx.get("type", ""),
                    invoice=tx.get("invoice", ""),
                    amount=tx.get("amount", 0),
                    fees_paid=tx.get("fees_paid", 0),
                    created_at=tx.get("created_at", 0),
                    settled_at=tx.get("settled_at"),
                    payment_hash=tx.get("payment_hash", ""),
                    preimage=tx.get("preimage", ""),
                    description=tx.get("description", ""),
                )
            )

        return ListTransactionsResponse(transactions=transactions)
