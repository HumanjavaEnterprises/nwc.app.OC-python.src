"""Pay a Lightning invoice and verify the payment."""

import asyncio
from nostrwalletconnect import NWCClient

NWC_URI = "nostr+walletconnect://<wallet_pubkey>?relay=wss://relay.example.com&secret=<hex_secret>"


async def main():
    async with NWCClient(NWC_URI) as nwc:
        # Pay an invoice
        bolt11 = "lnbc10u1p..."  # paste a real bolt11 invoice here
        payment = await nwc.pay_invoice(bolt11)
        print(f"Paid! Preimage: {payment.preimage}")

        # Verify the payment
        lookup = await nwc.lookup_invoice(invoice=bolt11)
        print(f"Invoice paid: {lookup.paid}")

        # List recent transactions
        history = await nwc.list_transactions(limit=5)
        for tx in history.transactions:
            direction = "received" if tx.type == "incoming" else "sent"
            print(f"  {direction} {tx.amount // 1000} sats — {tx.description}")


asyncio.run(main())
