# main.py

import customtkinter as ctk
from gui.login_frame import LoginFrame
from gui.main_dashboard import MainDashboard

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Crypto Sniper Bot")
        self.geometry("720x512")
        self.resizable(True, True)
        self._load_login()

    def _load_login(self):
        self.login_frame = LoginFrame(self, self._on_login_success)

    def _on_login_success(self, mnemonic):
        self.login_frame.destroy()
        self.dashboard = MainDashboard(self, mnemonic)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
