# NostrWalletConnect for OpenClaw

**Give your AI access to a Lightning wallet.**

A Python SDK for OpenClaw AI entities to connect to any NWC-compatible wallet and send payments, check balance, create invoices, and list transactions — all over the Nostr protocol via NIP-47.

## Why?

AI agents that can pay for things — API calls, compute, storage, services from other agents — need wallet access. NWC (Nostr Wallet Connect) gives them that without holding custody of funds. The wallet stays under the human's control. The agent gets a scoped connection string that authorizes specific operations.

**What your bot can do with NWC:**

- **Pay Lightning invoices** — your bot can pay for services, APIs, or other agents' work.
- **Create invoices to receive payment** — your bot can charge for its own services.
- **Check wallet balance** — know what's available before committing to a payment.
- **Verify payments** — look up whether an invoice was paid and get the preimage.
- **View transaction history** — audit trail of all payments sent and received.

All communication is NIP-44 encrypted over Nostr relays. The relay operator sees nothing but ciphertext.

## Install

```bash
pip install nostrwalletconnect
```

This also installs [nostrkey](https://pypi.org/project/nostrkey/) as a dependency (for Nostr identity, signing, and encryption).

## Quick Start

```python
import asyncio
from nostrwalletconnect import NWCClient

# Paste your NWC connection string from your wallet
NWC_URI = "nostr+walletconnect://<wallet_pubkey>?relay=wss://...&secret=<hex_secret>"

async def main():
    async with NWCClient(NWC_URI) as nwc:
        balance = await nwc.get_balance()
        print(f"Balance: {balance.balance // 1000} sats")

asyncio.run(main())
```

## Pay an Invoice

```python
async with NWCClient(NWC_URI) as nwc:
    result = await nwc.pay_invoice("lnbc10u1p...")
    print(f"Paid! Preimage: {result.preimage}")
```

## Create an Invoice

```python
async with NWCClient(NWC_URI) as nwc:
    invoice = await nwc.make_invoice(
        amount=50_000,  # millisatoshis
        description="Payment for AI service"
    )
    print(f"Invoice: {invoice.invoice}")
```

## Look Up an Invoice

```python
async with NWCClient(NWC_URI) as nwc:
    status = await nwc.lookup_invoice(payment_hash="abc123...")
    print(f"Paid: {status.paid}")
```

## List Transactions

```python
async with NWCClient(NWC_URI) as nwc:
    history = await nwc.list_transactions(limit=10)
    for tx in history.transactions:
        direction = "received" if tx.type == "incoming" else "sent"
        print(f"  {direction} {tx.amount // 1000} sats")
```

## NIP Implemented

| NIP | What | Status |
|-----|------|--------|
| NIP-47 | Nostr Wallet Connect | Implemented |

Built on top of nostrkey which implements NIP-01, NIP-19, NIP-44.

## OpenClaw Skill (ClawHub)

This repo includes an OpenClaw skill in `clawhub/` so AI agents can discover and use NostrWalletConnect directly from the [ClawHub registry](https://clawhub.ai/).

```bash
clawhub install nostrwalletconnect
```

## License

MIT
