# Installation

This guide is for **caregivers and end-users** installing PyMonitor on a Windows machine used with OptiKey/Tobii.

---

## Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10 or 11 (uses `wmi`, `psutil.win_service_get`, `sc`, `taskkill` - no Linux/macOS) |
| **Python** | 3.14+ (`pyproject.toml:6`) - check with `python --version` |
| **Privileges** | **Administrator** required for service restarts (`sc stop/start`) |
| **Tooling** | `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/)) |
| **Hardware** | Tobii Eye Tracker (optional), webcam (optional for `/photo`), speakers (for alarms) |

---

## 1. Get the Code

```bash
git clone https://github.com/your-org/pymonitor.git
cd pymonitor
```

Or download the `.exe` built via PyInstaller (see [Running](running.md) #Build).

## 2. Install Dependencies

```bash
uv sync
```

This creates `.venv/` and installs `python-telegram-bot`, `psutil`, `wmi`, `opencv-python-headless`, `playsound3`, `pydantic-settings`, etc. (`pyproject.toml:7`).

Verify:

```bash
uv run python -c "import psutil, telegram; print('ok')"
```

## 3. Verify Windows Services (Optional)

If you use Tobii, confirm services exist:

```powershell
sc query "Tobii Service"
sc query "TobiiGeneric"
sc query "TobiilS5LEYETRACKER5"
# If missing, adjust names in PYMONITOR__TOBII__* (see Configuration)
```

Check processes:

```powershell
tasklist | findstr /I "OptiKey AnyDesk Tobii"
```

## 4. Next Steps

Continue to [Configuration](configuration.md) to set `PYMONITOR__TELEGRAM__*` and hardware paths, then [Running](running.md) to start the daemon.

---

!!! warning "Administrator"
    Right-click your terminal / shortcut and **Run as Administrator**. Without it, `restart_tobii_service` will fail silently (logged at `app/services/pyagent.py`).

!!! tip "Headless?"
    PyMonitor runs with `--noconsole` when built as `.exe`. During setup, run from a console (`uv run main.py`) to see startup logs.
