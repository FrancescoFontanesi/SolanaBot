# Updated logic/wallet_manager.py with cached cumulative SOL deposits

import os
import json
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from nacl.signing import SigningKey
from bip_utils import Bip39SeedGenerator,Bip32Slip10Ed25519




CACHE_FILE = "data/sol_deposit_cache.json"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
client = Client(SOLANA_RPC_URL)


from bip_utils import Bip44, Bip39SeedGenerator, Bip44Coins, Bip32Slip10Ed25519

def load_wallet_from_mnemonic(mnemonic: str):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip32_ctx = Bip32Slip10Ed25519.FromSeed(seed_bytes)

    # Forza derivation path: m/44'/501'/0'/0'
    derivation_path = "m/44'/501'/0'/0'"
    derived = bip32_ctx.DerivePath(derivation_path)

    
    signing_key = SigningKey(derived.PrivateKey().Raw().ToBytes())
    keypair_bytes = signing_key.encode() + signing_key.verify_key.encode()


    return Keypair.from_bytes(keypair_bytes)


def get_wallet_balance(pubkey: Pubkey) -> float:
    response = client.get_balance(pubkey)
    lamports = response.value
    return lamports / 1e9

def load_cached_deposit(pubkey: str) -> float:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            return cache.get(pubkey, 0.0)
    return 0.0

def save_cached_deposit(pubkey: str, amount: float):
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
    cache[pubkey] = amount
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_total_sol_deposited(pubkey: Pubkey) -> float:
    """
    Returns the total SOL ever received by the wallet.
    Caches the result locally to avoid repeated heavy RPC calls.
    """
    pubkey_str = str(pubkey)
    cached = load_cached_deposit(pubkey_str)
    if cached > 0:
        return cached

    total_received = 0.0
    signatures = client.get_signatures_for_address(pubkey, limit=1000).value

    for sig in signatures:
        tx_data = client.get_transaction(sig["signature"], encoding="json")
        if not tx_data or not tx_data.get("result"):
            continue

        meta = tx_data["result"]["meta"]
        if not meta or meta.get("err"):
            continue

        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        accounts = tx_data["result"]["transaction"]["message"]["accountKeys"]

        if pubkey_str not in accounts:
            continue

        idx = accounts.index(pubkey_str)
        if idx >= len(pre_balances) or idx >= len(post_balances):
            continue

        delta = post_balances[idx] - pre_balances[idx]
        if delta > 0:
            total_received += delta / 1e9

    save_cached_deposit(pubkey_str, total_received)
    return round(total_received, 6)

def calculate_pnl(initial_deposit: float, current_balance: float) -> float:
    return round(current_balance - initial_deposit, 6)

from solders.pubkey import Pubkey
from solana.rpc.api import Client
from spl.token.constants import TOKEN_PROGRAM_ID

# già presente
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
client = Client(SOLANA_RPC_URL)


def get_token_portfolio(pubkey: Pubkey) -> list[dict]:
    """
    Ritorna una lista di dict con i token SPL (mint, amount, decimals).
    Solo quelli con amount > 0.
    """
    # Chiedo al nodo tutti gli account token di proprietà del pubkey
    resp = client.get_token_accounts_by_owner(
        Pubkey,
        opts=TOKEN_PROGRAM_ID,
    )
    result = []
    for wrapped in resp["result"]["value"]:
        info = wrapped["account"]["data"]["parsed"]["info"]
        mint = info["mint"]
        amt_raw = int(info["tokenAmount"]["amount"])
        decimals = int(info["tokenAmount"]["decimals"])
        amount = amt_raw / (10 ** decimals)
        if amount > 0:
            result.append({
                "mint": mint,
                "amount": amount,
                "decimals": decimals,
                "symbol": mint[:6]  # placeholder: i primi 6 caratteri del mint
            })
    return result

