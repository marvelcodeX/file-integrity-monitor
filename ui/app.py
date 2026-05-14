"""
ui/app.py
Main CustomTkinter application window.
Composes the Settings panel and Dashboard panel into a single window.
"""

import customtkinter as ctk
from ui.dashboard import DashboardPanel
from ui.settings import SettingsPanel


# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FIMApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("File Integrity Monitor")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)   # sidebar fixed
        self.grid_columnconfigure(1, weight=1)   # dashboard expands
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar (Settings) ────────────────────────────────────────────────
        self._sidebar = SettingsPanel(
            master=self,
            on_baseline_saved=self._on_baseline_saved,
            on_monitor_toggled=self._on_monitor_toggled,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # ── Main content (Dashboard) ───────────────────────────────────────────
        self._dashboard = DashboardPanel(master=self)
        self._dashboard.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_baseline_saved(self, directory: str, file_count: int):
        self._dashboard.post_system(
            f"Baseline created for {directory!r} — {file_count} file(s) hashed."
        )
        self._dashboard.update_status("idle", directory)

    def _on_monitor_toggled(self, running: bool, directory: str):
        if running:
            self._dashboard.post_system(f"Monitoring started on {directory!r}")
            self._dashboard.update_status("monitoring", directory)
        else:
            self._dashboard.post_system(f"Monitoring stopped.")
            self._dashboard.update_status("idle", directory)

    def alert_callback(self, event_type: str, filepath: str, detail: str):
        """Called from monitor thread — schedules UI update on main thread."""
        self.after(0, self._dashboard.post_alert, event_type, filepath, detail)