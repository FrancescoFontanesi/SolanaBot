# Re-executing after environment reset: logic/user_data_manager.py

import os
import json

DATA_DIR = "data/user_data"

def _get_user_file(pubkey: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{pubkey}.json")

def load_user_data(pubkey: str) -> dict:
    filepath = _get_user_file(pubkey)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {
        "parameters": {
            "take_profit": 2.0,
            "stop_loss": 10.0,
            "order_size": 0.1,
            "slippage": 1.0
        },
        "whales": []  # List of {"name": str, "address": str}
    }

def save_user_data(pubkey: str, data: dict):
    filepath = _get_user_file(pubkey)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
