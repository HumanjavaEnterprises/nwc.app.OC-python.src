"""Quick start — connect to a wallet and check balance."""

import asyncio
from nostrwalletconnect import NWCClient

# Paste your NWC connection string from your wallet app
NWC_URI = "nostr+walletconnect://<wallet_pubkey>?relay=wss://relay.example.com&secret=<hex_secret>"


async def main():
    async with NWCClient(NWC_URI) as nwc:
        # Check what the wallet supports
        info = await nwc.get_info()
        print(f"Wallet: {info.alias}")
        print(f"Supported methods: {info.methods}")

        # Check balance
        balance = await nwc.get_balance()
        print(f"Balance: {balance.balance} msats ({balance.balance // 1000} sats)")


asyncio.run(main())
