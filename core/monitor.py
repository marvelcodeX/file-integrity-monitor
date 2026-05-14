"""
core/monitor.py
Real-time file watching using watchdog.
Detects create / modify / delete events and compares against the baseline.
"""

import os
import threading
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)

from core.hasher import hash_file
from core.database import load_baseline
from core import logger as fim_logger


AlertCallback = Callable[[str, str, str], None]
# Signature: (event_type, filepath, detail)


class _FIMEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler that checks filesystem events against the baseline.
    Calls `alert_cb` whenever an anomaly is detected.
    """

    def __init__(self, directory: str, alert_cb: AlertCallback):
        super().__init__()
        self.directory = directory
        self.alert_cb = alert_cb
        self._baseline: dict[str, str] = load_baseline(directory)
        self._lock = threading.Lock()

    def refresh_baseline(self) -> None:
        with self._lock:
            self._baseline = load_baseline(self.directory)

    def _rel(self, abs_path: str) -> str:
        return str(Path(abs_path).relative_to(self.directory))

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_created(self, event):
        if event.is_directory:
            return
        rel = self._rel(event.src_path)
        with self._lock:
            if rel not in self._baseline:
                detail = "New file not in baseline"
                fim_logger.log_alert("CREATED", event.src_path, detail)
                self.alert_cb("CREATED", event.src_path, detail)

    def on_modified(self, event):
        if event.is_directory:
            return
        rel = self._rel(event.src_path)
        with self._lock:
            expected = self._baseline.get(rel)
        if expected is None:
            return  # File wasn't in baseline; creation event handles it

        current = hash_file(event.src_path)
        if current is None:
            detail = "File unreadable after modification event"
            fim_logger.log_alert("UNREADABLE", event.src_path, detail)
            self.alert_cb("UNREADABLE", event.src_path, detail)
        elif current != expected:
            detail = f"Hash mismatch | expected={expected[:12]}… | got={current[:12]}…"
            fim_logger.log_alert("MODIFIED", event.src_path, detail)
            self.alert_cb("MODIFIED", event.src_path, detail)

    def on_deleted(self, event):
        if event.is_directory:
            return
        rel = self._rel(event.src_path)
        with self._lock:
            if rel in self._baseline:
                detail = "File was in baseline — now deleted"
                fim_logger.log_alert("DELETED", event.src_path, detail)
                self.alert_cb("DELETED", event.src_path, detail)

    def on_moved(self, event):
        if event.is_directory:
            return
        src_rel = self._rel(event.src_path)
        dst_rel = self._rel(event.dest_path)
        with self._lock:
            in_baseline = src_rel in self._baseline
        if in_baseline:
            detail = f"Renamed/moved to {event.dest_path!r}"
            fim_logger.log_alert("MOVED", event.src_path, detail)
            self.alert_cb("MOVED", event.src_path, detail)


class FileMonitor:
    """
    High-level wrapper around watchdog Observer.
    Use start() / stop() to control monitoring.
    """

    def __init__(self, directory: str, alert_cb: AlertCallback):
        self.directory = directory
        self._handler = _FIMEventHandler(directory, alert_cb)
        self._observer: Observer | None = None
        self._running = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._observer = Observer()
        self._observer.schedule(self._handler, self.directory, recursive=True)
        self._observer.start()
        self._running = True
        fim_logger.log_monitor_started(self.directory)

    def stop(self) -> None:
        if not self._running or self._observer is None:
            return
        self._observer.stop()
        self._observer.join()
        self._running = False
        fim_logger.log_monitor_stopped(self.directory)

    def refresh_baseline(self) -> None:
        """Hot-reload the baseline without restarting the observer."""
        self._handler.refresh_baseline()

    @property
    def is_running(self) -> bool:
        return self._running