# Updated version of gui/login_frame.py

import tkinter as tk
import customtkinter as ctk
from logic.wallet_manager import load_wallet_from_mnemonic
import json
import os

LOGIN_DATA_FILE = "data/login_data.json"

def load_saved_mnemonic():
    if os.path.exists(LOGIN_DATA_FILE):
        with open(LOGIN_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("mnemonic")
    return None

def save_mnemonic(mnemonic):
    with open(LOGIN_DATA_FILE, "w") as f:
        json.dump({"mnemonic": mnemonic}, f)

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.grid(row=0, column=0, sticky="nsew")
        self.place(relx=0.5, rely=0.5, anchor="center")
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Inserisci la tua seed phrase (12 parole)", font=ctk.CTkFont(size=16)).pack(pady=10)

        self.phrase_frame = ctk.CTkFrame(self)
        self.phrase_frame.pack(pady=5)
        self.seed_entries = []
        for i in range(12):
            entry = ctk.CTkEntry(self.phrase_frame, width=80)
            entry.grid(row=i // 4, column=i % 4, padx=5, pady=5)
            self.seed_entries.append(entry)

        saved_mnemonic = load_saved_mnemonic()
        if saved_mnemonic:
            words = saved_mnemonic.split()
            for i in range(min(12, len(words))):
                self.seed_entries[i].insert(0, words[i])

        self.derived_label = ctk.CTkLabel(self, text="Wallet: non derivato", font=ctk.CTkFont(size=12))
        self.derived_label.pack(pady=(10, 0))

        self.remember_var = tk.BooleanVar()
        self.remember_check = ctk.CTkCheckBox(self, text="Ricordami", variable=self.remember_var)
        self.remember_check.pack(pady=(5, 10))

        self.login_button = ctk.CTkButton(self, text="Login", command=self.try_login)
        self.login_button.pack(pady=10)

    def try_login(self):
        mnemonic = " ".join([e.get().strip() for e in self.seed_entries])

        if len(mnemonic.split()) != 12:
            tk.messagebox.showerror("Errore", "Inserisci esattamente 12 parole.")
            return

        try:
            keypair = load_wallet_from_mnemonic(mnemonic)
            pubkey = keypair.pubkey
        except Exception as e:
            tk.messagebox.showerror("Errore", f"Seed non valida: {e}")
            return

        self.derived_label.configure(text=f"Wallet: {pubkey.__str__()}", text_color="green")

        if self.remember_var.get():
            save_mnemonic(mnemonic)

        self.on_login_success(mnemonic)

