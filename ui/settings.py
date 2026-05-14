"""
ui/settings.py
Sidebar: folder picker, baseline controls, monitor toggle.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable

from core.hasher import hash_directory
from core.database import save_baseline, load_baseline, baseline_exists, get_baseline_info, clear_baseline
from core.monitor import FileMonitor
from core import logger as fim_logger


class SettingsPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_baseline_saved: Callable[[str, int], None],
        on_monitor_toggled: Callable[[bool, str], None],
        **kwargs,
    ):
        super().__init__(master, width=280, corner_radius=12, **kwargs)
        self.grid_propagate(False)

        self._on_baseline_saved = on_baseline_saved
        self._on_monitor_toggled = on_monitor_toggled

        self._directory: str = ""
        self._monitor: FileMonitor | None = None
        self._monitoring = False

        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(10, weight=1)  # spacer row

        pad = {"padx": 16, "pady": 6}

        # ── App title ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="🔒 FIM",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color="#4ECDC4",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(20, 2))

        ctk.CTkLabel(
            self,
            text="File Integrity Monitor",
            font=ctk.CTkFont(size=11),
            text_color="#636E72",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        ctk.CTkFrame(self, height=1, fg_color="#2D3436").grid(
            row=2, column=0, sticky="ew", padx=16, pady=4
        )

        # ── Directory picker ──────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="WATCH DIRECTORY",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#B2BEC3",
        ).grid(row=3, column=0, sticky="w", **pad)

        self._dir_display = ctk.CTkLabel(
            self,
            text="None selected",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#636E72",
            wraplength=240,
            anchor="w",
            justify="left",
        )
        self._dir_display.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkButton(
            self,
            text="📂  Browse Folder",
            command=self._pick_directory,
            height=34,
            corner_radius=8,
        ).grid(row=5, column=0, sticky="ew", **pad)

        ctk.CTkFrame(self, height=1, fg_color="#2D3436").grid(
            row=6, column=0, sticky="ew", padx=16, pady=8
        )

        # ── Baseline controls ─────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="BASELINE SNAPSHOT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#B2BEC3",
        ).grid(row=7, column=0, sticky="w", **pad)

        self._baseline_info = ctk.CTkLabel(
            self,
            text="No baseline stored",
            font=ctk.CTkFont(size=10),
            text_color="#636E72",
            wraplength=240,
            anchor="w",
            justify="left",
        )
        self._baseline_info.grid(row=8, column=0, sticky="w", padx=16, pady=(0, 6))

        self._btn_baseline = ctk.CTkButton(
            self,
            text="📸  Create Baseline",
            command=self._create_baseline,
            height=34,
            corner_radius=8,
            fg_color="#00B894",
            hover_color="#00A381",
        )
        self._btn_baseline.grid(row=9, column=0, sticky="ew", **pad)

        self._btn_clear = ctk.CTkButton(
            self,
            text="🗑  Clear Baseline",
            command=self._clear_baseline,
            height=28,
            corner_radius=8,
            fg_color="#2D3436",
            hover_color="#D63031",
            font=ctk.CTkFont(size=11),
        )
        self._btn_clear.grid(row=10, column=0, sticky="ew", padx=16, pady=(0, 4))

        # ── Spacer ────────────────────────────────────────────────────────────
        ctk.CTkFrame(self, fg_color="transparent").grid(row=11, column=0, sticky="nsew")

        ctk.CTkFrame(self, height=1, fg_color="#2D3436").grid(
            row=12, column=0, sticky="ew", padx=16, pady=8
        )

        # ── Monitor toggle ────────────────────────────────────────────────────
        self._btn_monitor = ctk.CTkButton(
            self,
            text="▶  Start Monitoring",
            command=self._toggle_monitor,
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#0984E3",
            hover_color="#0773C5",
        )
        self._btn_monitor.grid(row=13, column=0, sticky="ew", padx=16, pady=(0, 8))

        # ── Progress bar (hashing feedback) ───────────────────────────────────
        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", height=6)
        self._progress.grid(row=14, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._progress.set(0)
        self._progress.grid_remove()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _pick_directory(self):
        chosen = filedialog.askdirectory(title="Select directory to monitor")
        if not chosen:
            return
        self._directory = chosen
        short = chosen if len(chosen) < 38 else "…" + chosen[-35:]
        self._dir_display.configure(text=short, text_color="#DFE6E9")
        self._refresh_baseline_info()

    def _create_baseline(self):
        if not self._directory:
            messagebox.showwarning("No Directory", "Please select a directory first.")
            return
        if self._monitoring:
            messagebox.showwarning("Monitoring Active", "Stop monitoring before re-baselining.")
            return

        self._btn_baseline.configure(state="disabled", text="Hashing…")
        self._progress.grid()
        self._progress.start()

        def _worker():
            try:
                hashes = hash_directory(self._directory)
                save_baseline(self._directory, hashes)
                fim_logger.log_baseline_created(self._directory, len(hashes))
                self.after(0, self._baseline_saved_cb, len(hashes))
            except Exception as e:
                self.after(0, self._baseline_error_cb, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _baseline_saved_cb(self, count: int):
        self._progress.stop()
        self._progress.grid_remove()
        self._btn_baseline.configure(state="normal", text="📸  Create Baseline")
        self._refresh_baseline_info()
        self._on_baseline_saved(self._directory, count)

    def _baseline_error_cb(self, error: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._btn_baseline.configure(state="normal", text="📸  Create Baseline")
        messagebox.showerror("Baseline Error", f"Failed to create baseline:\n{error}")

    def _clear_baseline(self):
        if not self._directory:
            return
        if messagebox.askyesno("Clear Baseline", f"Delete baseline for:\n{self._directory}?"):
            clear_baseline(self._directory)
            self._refresh_baseline_info()

    def _toggle_monitor(self):
        if not self._directory:
            messagebox.showwarning("No Directory", "Please select a directory first.")
            return
        if not baseline_exists(self._directory):
            messagebox.showwarning("No Baseline", "Create a baseline snapshot before monitoring.")
            return

        if self._monitoring:
            self._stop_monitor()
        else:
            self._start_monitor()

    def _start_monitor(self):
        # Retrieve the alert_callback from the root FIMApp
        root = self.winfo_toplevel()
        alert_cb = root.alert_callback

        self._monitor = FileMonitor(self._directory, alert_cb)
        self._monitor.start()
        self._monitoring = True
        self._btn_monitor.configure(
            text="⏹  Stop Monitoring",
            fg_color="#D63031",
            hover_color="#B71C1C",
        )
        self._on_monitor_toggled(True, self._directory)

    def _stop_monitor(self):
        if self._monitor:
            self._monitor.stop()
            self._monitor = None
        self._monitoring = False
        self._btn_monitor.configure(
            text="▶  Start Monitoring",
            fg_color="#0984E3",
            hover_color="#0773C5",
        )
        self._on_monitor_toggled(False, self._directory)

    def _refresh_baseline_info(self):
        if not self._directory or not baseline_exists(self._directory):
            self._baseline_info.configure(text="No baseline stored", text_color="#636E72")
            return
        info = get_baseline_info(self._directory)
        ts = info["last_updated"] or "unknown"
        count = info["file_count"]
        self._baseline_info.configure(
            text=f"{count} file(s)\nLast: {ts}",
            text_color="#00B894",
        )