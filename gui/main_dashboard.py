import tkinter as tk
import customtkinter as ctk
from logic.wallet_manager import (
    load_wallet_from_mnemonic,
    get_wallet_balance,
    get_total_sol_deposited,
    calculate_pnl,
    get_token_portfolio
)
from logic.user_data_manager import load_user_data, save_user_data
import threading
from logic.wallet_tracker_telegram_async import start_listener, stop_listener



class MainDashboard(ctk.CTkFrame):
    def __init__(self, master, mnemonic):
        super().__init__(master)
        self._stop_event      = None
        self._listener_thread = None

        self.master = master
        self.mnemonic = mnemonic
        self.keypair = load_wallet_from_mnemonic(mnemonic)
        self.public_key = str(self.keypair.pubkey())
        self.user_data = load_user_data(self.public_key)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

        # Imposta dimensioni minime e fill
        self.master.minsize(800, 700)
        self.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Definisci 2 col e 3 righe invertendo log e contenuto centrale
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=0)  # stats
        self.grid_rowconfigure(1, weight=2)  # log ora row1
        self.grid_rowconfigure(2, weight=1)  # middle ora row2

        # — RIGA0: Statistiche wallet —
        self.stats_frame = ctk.CTkFrame(self, corner_radius=10)
        self.stats_frame.grid(row=0, column=0, columnspan=2,
                              padx=15, pady=(15,10), sticky="ew")
        self._build_wallet_stats()

        # — RIGA1: Activity Log —
        self.log_frame = ctk.CTkFrame(self, corner_radius=10, height=150)
        self.log_frame.grid(row=1, column=0, columnspan=2,
                             padx=15, pady=(0,10), sticky="nsew")
        self.log_frame.grid_propagate(True)
        self._build_log_frame()

        # — RIGA2,COL0: Parametri bot —
        self.param_frame = ctk.CTkFrame(self, corner_radius=10)
        self.param_frame.grid(row=2, column=0,
                              padx=(15,8), pady=10, sticky="nsew")
        self._build_param_frame()

        # — RIGA2,COL1: Token Portfolio —
        self.portfolio_frame = ctk.CTkFrame(self, corner_radius=10)
        self.portfolio_frame.grid(row=2, column=1,
                                  padx=(8,15), pady=10, sticky="nsew")
        self._build_portfolio_frame()

    def _build_wallet_stats(self):
        bal = get_wallet_balance(self.keypair.pubkey())
        dep = get_total_sol_deposited(self.keypair.pubkey())
        pnl = calculate_pnl(dep, bal)
        info = (
            f"Wallet: {self.public_key}\n"
            f"Balance: {bal:.4f} SOL\n"
            f"Initial Deposit: {dep:.4f} SOL\n"
            f"PnL: {pnl:+.4f} SOL"
        )
        lbl = ctk.CTkLabel(self.stats_frame, text=info, justify="left",
                            font=ctk.CTkFont(size=14))
        lbl.pack(padx=10, pady=10, fill="x")

    def _build_param_frame(self):
        p = self.user_data["parameters"]
        n = 1 + 4 + 1
        self.param_frame.grid_rowconfigure(0, weight=1)
        for i in range(1, n+1): self.param_frame.grid_rowconfigure(i, weight=0)
        self.param_frame.grid_rowconfigure(n+1, weight=1)
        self.param_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.param_frame, text="Bot Parameters",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .grid(row=1, column=0, pady=5, sticky="ew")

        fields = [("take_profit","Take Profit Multiplier"),
                  ("stop_loss","Stop Loss (%)"),
                  ("order_size","Order Size (SOL)"),
                  ("slippage","Slippage (%)")]
        for idx,(k,ph) in enumerate(fields, start=2):
            e = ctk.CTkEntry(self.param_frame, placeholder_text=ph)
            e.insert(0, str(p[k])); setattr(self, k, e)
            e.grid(row=idx, column=0, padx=10, pady=3, sticky="ew")

        ctk.CTkButton(self.param_frame, text="Start Bot",
                      command=self._start_bot)\
            .grid(row=n, column=0, pady=10)
        ctk.CTkButton(self.param_frame, text="Stop Bot",
                      command=self._stop_bot)\
            .grid(row=n+1, column=0, pady=10)

    def _build_portfolio_frame(self):
        self.portfolio_frame.grid_columnconfigure((0,1,2), weight=1)
        self.portfolio_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.portfolio_frame, text="Token Portfolio",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .grid(row=0, column=0, columnspan=3,
                  pady=(10,5), sticky="ew")

        self.portfolio_grid = ctk.CTkFrame(self.portfolio_frame)
        self.portfolio_grid.grid(row=1, column=0, columnspan=3,
                                 padx=10, pady=(0,10), sticky="nsew")
        for c in range(3): self.portfolio_grid.grid_columnconfigure(c, weight=1)
        for i,txt in enumerate(["Token","PnL","Action"]):
            ctk.CTkLabel(self.portfolio_grid, text=txt,
                         font=ctk.CTkFont(weight="bold"))\
                .grid(row=0,column=i,sticky="ew",padx=5)
        self._portfolio_tokens = get_token_portfolio(self.keypair.pubkey())
        self._refresh_portfolio_display()

    def _refresh_portfolio_display(self):
        for w in self.portfolio_grid.winfo_children()[3:]: w.destroy()
        for i,itm in enumerate(self._portfolio_tokens, start=1):
            ctk.CTkLabel(self.portfolio_grid, text=itm["symbol"])\
                .grid(row=i,column=0,sticky="ew",padx=5,pady=2)
            ctk.CTkLabel(self.portfolio_grid, text=f"{itm['amount']:.6f}")\
                .grid(row=i,column=1,sticky="ew",padx=5,pady=2)
            ctk.CTkButton(self.portfolio_grid,text="Sell",
                          command=lambda m=itm["mint"]: self._sell_token(m))\
                .grid(row=i,column=2,sticky="ew",padx=5,pady=2)

    def _build_log_frame(self):
        self.log_frame.grid_rowconfigure(0,weight=0)
        self.log_frame.grid_rowconfigure(1,weight=1)
        self.log_frame.grid_columnconfigure(0,weight=1)

        ctk.CTkLabel(self.log_frame, text="Activity Log",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .grid(row=0,column=0,pady=5,sticky="ew")

        log_container = ctk.CTkFrame(self.log_frame, corner_radius=0)
        log_container.grid(row=1,column=0,sticky="nsew",padx=10,pady=(0,10))
        log_container.grid_rowconfigure(0,weight=1)
        log_container.grid_columnconfigure(0,weight=1)
        log_container.grid_columnconfigure(1,weight=0)

        self.log_text = ctk.CTkTextbox(log_container, height=80)
        self.log_text.grid(row=0,column=0,sticky="nsew")
        scrollbar = ctk.CTkScrollbar(log_container, command=self.log_text.yview)
        scrollbar.grid(row=0,column=1,sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self._log("Dashboard loaded.")
        self._log("Log system initialized.")

    def _log(self, message):
        self.log_text.insert(tk.END, f"[LOG] {message}\n")
        self.log_text.see(tk.END)

    def _sell_token(self, token):
        self._log(f"Sell requested for {token} (not implemented)")

    def _start_bot(self):
        try:
            tp=float(self.take_profit.get()); sl=float(self.stop_loss.get())
            sz=float(self.order_size.get()); sp=float(self.slippage.get())
            if tp<=1 or sl<=0 or sz<=0 or sp<=0: raise ValueError
        except ValueError:
            return self._log("Invalid bot parameters.")
        self.user_data["parameters"]={"take_profit":tp,
                                       "stop_loss":sl,
                                       "order_size":sz,
                                       "slippage":sp}
        self._log(f"Bot started with: TP {tp}x, SL {sl}%, Size {sz} SOL, Slippage {sp}%")
        # Prepara e avvia il listener Telegram
        self._stop_event = threading.Event()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        # start_listener(log_callback, stop_event) restituisce il Thread
        self._listener_thread = start_listener(self._log, self._stop_event)
    
    def _stop_bot(self):
    # Segnala al listener di fermarsi
        if self._stop_event:
            stop_listener(self._stop_event)
            self._stop_event = None

        # Se c’è un thread in esecuzione, attendi un breve join
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1)
            self._listener_thread = None

        # Aggiorna lo stato dei pulsanti
        self.stop_button.configure(state="disabled")
        self.start_button.configure(state="normal")

        # Log
        self._log("Bot Telegram fermato.")

    def _on_close(self):
        save_user_data(self.public_key, self.user_data)
        self.master.destroy()
