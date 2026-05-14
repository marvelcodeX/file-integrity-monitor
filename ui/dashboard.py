"""
ui/dashboard.py
Live alerts feed + status panel.
"""

import customtkinter as ctk
from datetime import datetime


# ── Color palette ─────────────────────────────────────────────────────────────
COLORS = {
    "MODIFIED":   "#FF6B35",   # orange
    "CREATED":    "#4ECDC4",   # teal
    "DELETED":    "#FF4757",   # red
    "MOVED":      "#FFA502",   # amber
    "UNREADABLE": "#A29BFE",   # lavender
    "SYSTEM":     "#74B9FF",   # light blue
}

STATUS_COLORS = {
    "idle":       "#636E72",
    "monitoring": "#00B894",
    "error":      "#D63031",
}

EVENT_ICONS = {
    "MODIFIED":   "✏️",
    "CREATED":    "➕",
    "DELETED":    "🗑️",
    "MOVED":      "📦",
    "UNREADABLE": "⚠️",
    "SYSTEM":     "ℹ️",
}


class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self._alert_count = 0
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="🛡  Live Alert Feed",
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._status_badge = ctk.CTkLabel(
            header,
            text="● IDLE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=STATUS_COLORS["idle"],
        )
        self._status_badge.grid(row=0, column=1, sticky="e")

        self._counter_label = ctk.CTkLabel(
            header,
            text="Alerts: 0",
            font=ctk.CTkFont(size=11),
            text_color="#B2BEC3",
        )
        self._counter_label.grid(row=1, column=0, sticky="w")

        self._dir_label = ctk.CTkLabel(
            header,
            text="No directory selected",
            font=ctk.CTkFont(size=11),
            text_color="#636E72",
        )
        self._dir_label.grid(row=1, column=1, sticky="e")

        # ── Scrollable alert list ─────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self,
            label_text="",
            fg_color=("#1a1a2e", "#0f0f1a"),
            corner_radius=8,
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self._scroll.grid_columnconfigure(0, weight=1)

        # ── Footer: clear button ──────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkButton(
            footer,
            text="Clear Feed",
            width=100,
            height=28,
            corner_radius=6,
            fg_color="#2D3436",
            hover_color="#636E72",
            command=self._clear_feed,
        ).pack(side="right")

        self._row_idx = 0

    # ── Public methods ────────────────────────────────────────────────────────

    def post_alert(self, event_type: str, filepath: str, detail: str):
        """Add an alert row to the feed (call from main thread only)."""
        self._alert_count += 1
        self._counter_label.configure(text=f"Alerts: {self._alert_count}")
        color = COLORS.get(event_type, "#FFFFFF")
        icon = EVENT_ICONS.get(event_type, "🔔")
        ts = datetime.now().strftime("%H:%M:%S")

        row = _AlertRow(
            self._scroll,
            timestamp=ts,
            event_type=event_type,
            icon=icon,
            filepath=filepath,
            detail=detail,
            accent=color,
        )
        row.grid(row=self._row_idx, column=0, sticky="ew", padx=4, pady=3)
        self._row_idx += 1

        # Auto-scroll to bottom
        self._scroll._parent_canvas.yview_moveto(1.0)

    def post_system(self, message: str):
        """Add an informational system message."""
        ts = datetime.now().strftime("%H:%M:%S")
        row = _AlertRow(
            self._scroll,
            timestamp=ts,
            event_type="SYSTEM",
            icon=EVENT_ICONS["SYSTEM"],
            filepath=message,
            detail="",
            accent=COLORS["SYSTEM"],
        )
        row.grid(row=self._row_idx, column=0, sticky="ew", padx=4, pady=3)
        self._row_idx += 1
        self._scroll._parent_canvas.yview_moveto(1.0)

    def update_status(self, status: str, directory: str = ""):
        color = STATUS_COLORS.get(status, "#FFFFFF")
        label = status.upper()
        self._status_badge.configure(text=f"● {label}", text_color=color)
        if directory:
            short = directory if len(directory) < 50 else "…" + directory[-47:]
            self._dir_label.configure(text=short)

    def _clear_feed(self):
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._row_idx = 0
        self._alert_count = 0
        self._counter_label.configure(text="Alerts: 0")


# ── Alert row widget ──────────────────────────────────────────────────────────

class _AlertRow(ctk.CTkFrame):
    def __init__(self, master, timestamp, event_type, icon, filepath, detail, accent, **kwargs):
        super().__init__(
            master,
            corner_radius=6,
            fg_color=("#1e1e2e", "#12121f"),
            border_width=1,
            border_color=accent,
            **kwargs,
        )
        self.grid_columnconfigure(1, weight=1)

        # Accent strip
        strip = ctk.CTkFrame(self, width=4, fg_color=accent, corner_radius=0)
        strip.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 8))

        # Top row: icon + type + timestamp
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(6, 0))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top,
            text=f"{icon} {event_type}",
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            text_color=accent,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top,
            text=timestamp,
            font=ctk.CTkFont(size=11),
            text_color="#636E72",
        ).grid(row=0, column=1, sticky="e")

        # File path
        ctk.CTkLabel(
            self,
            text=filepath,
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color="#DFE6E9",
            anchor="w",
            wraplength=600,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(2, 0))

        # Detail (optional)
        if detail:
            ctk.CTkLabel(
                self,
                text=detail,
                font=ctk.CTkFont(size=10),
                text_color="#636E72",
                anchor="w",
                wraplength=600,
            ).grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(0, 6))
        else:
            self.grid_rowconfigure(1, pad=6)