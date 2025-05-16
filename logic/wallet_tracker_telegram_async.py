# logic/telegram_whale_listener.py

import asyncio
import threading
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityTextUrl
import re
import json
from solana.rpc.api import Client
from logic.wallet_tracker_telegram import (
    parse_message_text,
    extract_signature_from_entities,
    get_token_address_from_signature
)

# Configura qui API e username
API_ID        = 25311096
API_HASH      = '7d2c845d1c873b1aa441364df5c560f3'
BOT_USERNAME  = 'Cielo_free_7_bot'
solana_client = Client("https://api.mainnet-beta.solana.com")



async def _listener_async(log_callback, stop_event):
    client = TelegramClient('session_cielo', API_ID, API_HASH)
    await client.start()
    me = await client.get_entity(BOT_USERNAME)

    @client.on(events.NewMessage(from_users=me.id))
    async def handler(event):
        if stop_event.is_set():
            await client.disconnect()
            return
        text      = event.message.message
        parsed    = parse_message_text(text)
        signature = extract_signature_from_entities(event)
        log_callback(f"🔔 Msg: {text} (sig: {signature})")
        if parsed and signature:
            mint = get_token_address_from_signature(signature)
            if mint:
                log_callback("🚨 BUY DETECTED")
                log_callback(f"    Token: {parsed['token_name']} ({mint}) on {parsed['platform']}")

    log_callback("🤖 Telegram listener avviato.")
    await client.run_until_disconnected()

def start_listener(log_callback, stop_event):
    """
    Avvia il listener in un thread separato.
    `log_callback` deve essere una funzione sincrona che accetta una stringa.
    `stop_event` è threading.Event().
    """
    thread = threading.Thread(
        target=lambda: asyncio.run(_listener_async(log_callback, stop_event)),
        daemon=True
    )
    thread.start()
    return thread

def stop_listener(stop_event):
    """
    Segnala al listener di fermarsi.
    """
    stop_event.set()
