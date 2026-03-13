"""Response types for NIP-47 Nostr Wallet Connect methods."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BalanceResponse:
    """Response from get_balance."""

    balance: int  # millisatoshis


@dataclass
class PayResponse:
    """Response from pay_invoice."""

    preimage: str  # hex-encoded payment preimage


@dataclass
class MakeInvoiceResponse:
    """Response from make_invoice."""

    invoice: str  # bolt11 payment request string
    payment_hash: str  # hex-encoded payment hash


@dataclass
class LookupInvoiceResponse:
    """Response from lookup_invoice."""

    invoice: str  # bolt11 payment request string
    paid: bool
    preimage: str | None = None


@dataclass
class Transaction:
    """A single transaction from list_transactions."""

    type: str  # "incoming" or "outgoing"
    invoice: str  # bolt11
    amount: int  # millisatoshis
    fees_paid: int  # millisatoshis
    created_at: int  # unix timestamp
    settled_at: int | None = None
    payment_hash: str = ""
    preimage: str = ""
    description: str = ""


@dataclass
class ListTransactionsResponse:
    """Response from list_transactions."""

    transactions: list[Transaction] = field(default_factory=list)


@dataclass
class GetInfoResponse:
    """Response from get_info."""

    alias: str = ""
    color: str = ""
    pubkey: str = ""
    network: str = ""
    block_height: int = 0
    block_hash: str = ""
    methods: list[str] = field(default_factory=list)


@dataclass
class NWCError:
    """Error response from the wallet service."""

    code: str  # e.g. "INSUFFICIENT_BALANCE", "NOT_FOUND", "INTERNAL"
    message: str
