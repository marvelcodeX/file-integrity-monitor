# 🔒 File Integrity Monitor (FIM)

A desktop cybersecurity tool that watches files for unauthorized changes using SHA-256 hashing and real-time filesystem monitoring.

---

## Features

- **SHA-256 baseline snapshots** stored in SQLite
- **Real-time watchdog monitoring** — detects create / modify / delete / move events instantly
- **Tamper-evident logging** — each log line is HMAC-signed
- **Modern CustomTkinter UI** — dark-themed dashboard with color-coded alert feed
- **Thread-safe** — monitoring runs in background threads, UI stays responsive

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python main.py
```

### 3. Usage workflow

1. Click **Browse Folder** and select a directory to protect.
2. Click **Create Baseline** — the app hashes every file and saves the snapshot.
3. Click **Start Monitoring** — watchdog begins watching in real time.
4. Any file change triggers a **color-coded alert** in the dashboard.
5. Click **Stop Monitoring** when done.

---

## Project Structure

```
file-integrity-monitor/
│
├── main.py                  # Entry point
├── core/
│   ├── hasher.py            # SHA-256 hashing (files & directories)
│   ├── monitor.py           # Watchdog event handler + FileMonitor class
│   ├── database.py          # SQLite baseline CRUD
│   └── logger.py            # HMAC-signed tamper-evident log writer
│
├── ui/
│   ├── app.py               # Main CTk window — wires settings ↔ dashboard
│   ├── dashboard.py         # Live alert feed + status panel
│   └── settings.py          # Sidebar: folder picker, baseline controls, toggle
│
├── logs/
│   └── fim.log              # Auto-generated — DO NOT edit manually
│
├── data/
│   └── baseline.db          # SQLite database — auto-generated
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Alert Types

| Icon | Type | Meaning |
|------|------|---------|
| ✏️ | MODIFIED | File hash changed vs baseline |
| ➕ | CREATED | New file not present at baseline time |
| 🗑️ | DELETED | Baseline file was deleted |
| 📦 | MOVED | Baseline file was renamed or moved |
| ⚠️ | UNREADABLE | File exists but cannot be read |

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.11+ |
| UI | CustomTkinter |
| Hashing | hashlib (SHA-256, built-in) |
| File watching | watchdog |
| Database | sqlite3 (built-in) |
| Logging | logging + HMAC signing |

---

## Security Notes

- Log lines include an HMAC-SHA256 signature generated from a per-session key. Any post-hoc edits to `fim.log` will produce signature mismatches.
- The baseline DB (`baseline.db`) should be stored on a separate, read-only volume in production deployments for stronger tamper resistance.
- This tool is for **detection**, not **prevention**. Pair it with proper access controls.