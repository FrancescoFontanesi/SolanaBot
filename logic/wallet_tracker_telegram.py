
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityTextUrl
import asyncio
import re
import json
from solana.rpc.api import Client

# API da configurare
API_ID = '25311096'
API_HASH = '7d2c845d1c873b1aa441364df5c560f3'
BOT_USERNAME = 'Cielo_free_7_bot'  # senza @


client = TelegramClient('session_cielo', API_ID, API_HASH)
solana_client = Client("https://api.mainnet-beta.solana.com")

# Estrai url firmato da ViewTx link
def extract_signature_from_entities(event) -> str | None:
    if event.message.entities:
        for entity in event.message.entities:
            if isinstance(entity, MessageEntityTextUrl):
                url = entity.url
                match = re.search(r'/tx/([\w\d]{32,88})', url)
                if match:
                    return match.group(1)
    return None

# Parser testo telegram per token name e piattaforma
def parse_message_text(text: str):
    try:
        match = re.search(
            r"Swapped ([\d.]+) #?SOL.*?for ([\d,\.]+) #?([\w\-]+).*?On #?(\w+).*?@ \$([\d\.]+)",
            text,
            re.IGNORECASE
        )
        if match:
            sol_amount, token_amount, token_name, platform, price = match.groups()
            if float(sol_amount) >= 0.90:
                return {
                    "sol_amount": float(sol_amount),
                    "token_name": token_name,
                    "platform": platform,
                    "price_usd": float(price)
                }
    except Exception as e:
        print(f"[Parser Error] {e}")
    return None

# RPC → token address from signature
def get_token_address_from_signature(signature: str) -> str | None:
    try:
        tx_data = solana_client.get_transaction(signature, encoding="jsonParsed", max_supported_transaction_version=0).value
        if not tx_data:
            return None
        tx_json = json.loads(tx_data.to_json())
        meta = tx_json.get("meta", {})
        post_balances = meta.get("postTokenBalances", [])
        for balance in post_balances:
            mint = balance.get("mint")
            owner = balance.get("owner")
            if mint and owner and not mint.startswith("So111"):
                return mint
        return None
    except Exception as e:
        print(f"[TX ERROR] {e}")
        return None

# Listener principale
async def setup_listener():
    await client.start()
    cielo_entity = await client.get_entity(BOT_USERNAME)
    cielo_user_id = cielo_entity.id

    @client.on(events.NewMessage(from_users=cielo_user_id))
    async def handler(event):
        text = event.message.message
        parsed = parse_message_text(text)
        signature = extract_signature_from_entities(event)
        print(f"🔔 New message from @{BOT_USERNAME}: {text} \n with signature: {signature}" )

        if parsed and signature:
            token_address = get_token_address_from_signature(signature)
            if token_address:
                print("🚨 BUY DETECTED")
                print(f"  Token Name: {parsed['token_name']}")
                print(f"  Token Address: {token_address}")
                print(f"  Platform: {parsed['platform']}")

    print(f"🤖 Listening to messages from @{BOT_USERNAME}...")
    await client.run_until_disconnected()


# Avvio
if __name__ == "__main__":
    asyncio.run(setup_listener()) 