# PyMonitor

> **Windows companion for ALS users** — Keep OptiKey, Tobii Eye Tracker 5, AnyDesk and essential hardware alive. Notify caregivers instantly via Telegram.

PyMonitor is an open-source, Windows-only monitoring daemon built for people with ALS who rely on assistive technologies like **OptiKey** and **Tobii**. It runs in the background, polls system health every few seconds, and — only when a status changes — sends an HTML message to Telegram and plays an audible alarm.

---

## Binaries — GitHub Releases

Pre-built Windows executables are published in **GitHub Releases**. You do not need to build from source if you just want to run PyMonitor.

- **Latest available:** `v1.1.0` — find the `PyMonitor.exe` asset at [github.com/ThalesArakawa/pymonitor/releases](https://github.com/ThalesArakawa/pymonitor/releases)
- Each release contains:
  - `PyMonitor.exe` — single-file, `--noconsole` build (`PyInstaller`)
  - `assets/` — required alarm sounds (`Charger-*.mp3`, `Tobii_*.mp3`)
  - `.env.example` — configuration template

> **Observation:** Binaries are distributed exclusively via GitHub Releases. No installer is provided — download the `.exe`, place `assets/` and `.env` beside it, and run **as Administrator** (see [Running](#running)).

```bash
# Example: download and verify v1.1.0
curl -LO https://github.com/ThalesArakawa/pymonitor/releases/download/v1.1.0/PyMonitor.exe
curl -LO https://github.com/ThalesArakawa/pymonitor/releases/download/v1.1.0/assets.zip
# Place .env beside PyMonitor.exe and run as Administrator
./PyMonitor.exe
```

Check [docs/getting-started/installation.md](docs/getting-started/installation.md) for detailed Windows setup and [docs/getting-started/running.md](docs/getting-started/running.md) for production deployment.

---

## What It Does

| Capability | Details |
|---|---|
| **7 Monitors** | Locked OS, OptiKey, AnyDesk, Network, Charger/Battery, Tobii Hardware, Tobii Services (`app/services/metrics.py`) |
| **Auto-Remediation** | Restarts Tobii services (`sc stop/start`), OptiKey and AnyDesk processes (`taskkill` + relaunch) — requires Administrator |
| **Telegram Bot** | Commands `/status`, `/log`, `/photo` (optional webcam snapshot) |
| **Alarms** | Repeating `Charger-nok.mp3` / `Tobii_Hardware` sounds via `playsound3` until the issue clears |
| **In-Memory State** | `StateManager` deduplicates — notified only on transitions (`True` <-> `False`) |

## Architecture at a Glance

```kroki-plantuml
@startuml
skinparam shadowing false
skinparam roundcorner 8
skinparam DefaultFontName "Roboto"

actor "Caregiver" as CG
participant "Telegram" as TG

box "PyMonitor (Windows)" #F4F5F7
  participant "MetricsService" as MS
  participant "PyAgent" as PA
  database "StateManager" as SM
  participant "AlarmService" as AL
end box

CG -> TG : /status /log /photo
TG -> PA : Bot API polling
MS -> SM : Event deduplication
MS -> PA : EventQueue
PA -> TG : HTML messages
PA -> AL : audible alerts
@enduml
```

See [Architecture Overview](docs/architecture/c4.md) and [Sequence Flows](docs/architecture/sequence_diagram.md) for full C4 and Kroki diagrams.

---

## Quick Start (From Source)

### Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11 (uses `wmi`, `psutil.win_service_get`, `sc`, `taskkill`) |
| **Python** | 3.14+ |
| **Privileges** | Administrator for service restarts |
| **Tooling** | `uv` — [install](https://docs.astral.sh/uv/getting-started/installation/) |

### Setup

```bash
# 1. Clone
git clone https://github.com/ThalesArakawa/pymonitor.git
cd pymonitor

# 2. Install dependencies
uv sync

# 3. Configure — copy and fill secrets
cp .env.example .env
# Edit .env: PYMONITOR__USE_TELEGRAM, PYMONITOR__TELEGRAM__BOT_TOKEN, PYMONITOR__TELEGRAM__CHAT_ID

# 4. Run (Administrator terminal)
uv run main.py

# 5. Preview docs
uv run properdocs serve
# -> http://127.0.0.1:8000
```

---

## Configuration

PyMonitor uses `pydantic-settings` (`app/settings.py`) with prefix `PYMONITOR__` and nested delimiter `__`. All settings can be set via environment variable or `.env` (`env_file=".env"`). Secrets are never hardcoded.

Minimal `.env` for Telegram:

```ini
PYMONITOR__USE_TELEGRAM=true
PYMONITOR__TELEGRAM__BOT_TOKEN=123456:ABC-your-token-from-BotFather
PYMONITOR__TELEGRAM__CHAT_ID=987654321
PYMONITOR__USE_ALARM_SOUND=true
PYMONITOR__MONITORING__CHECK_INTERVAL=10
```

Full variable reference:

```bash
# Tobii / OptiKey
PYMONITOR__TOBII__OPTIKEY_EXE_NAME=OptiKey.exe
PYMONITOR__TOBII__OPTIKEY_PATH=C:\OptiKey\OptiKey.exe
PYMONITOR__TOBII__EYEX_ENGINE_EXE_NAME=Tobii.EyeX.Engine.exe
PYMONITOR__TOBII__EYEX_INTERACTION_EXE_NAME=Tobii.EyeX.Interaction.exe
PYMONITOR__TOBII__SERVICE_EXE_NAME=Tobii.Service.exe
PYMONITOR__TOBII__SERVICE_NAME=Tobii Service
PYMONITOR__TOBII__GENERIC_NAME=TobiiGeneric
PYMONITOR__TOBII__EYETRACKER_NAME=TobiilS5LEYETRACKER5

# Telegram
PYMONITOR__USE_TELEGRAM=true
PYMONITOR__TELEGRAM__BOT_TOKEN=your-token
PYMONITOR__TELEGRAM__CHAT_ID=your-chat-id

# Monitoring
PYMONITOR__MONITORING__PHOTO_MODE=false
PYMONITOR__MONITORING__CHECK_INTERVAL=10

# Remote Access
PYMONITOR__REMOTE_ACCESS__ANYDESK_EXE_NAME=AnyDesk.exe
PYMONITOR__REMOTE_ACCESS__ANYDESK_PATH=C:\AnyDesk\AnyDesk.exe

# Alarm
PYMONITOR__USE_ALARM_SOUND=true
PYMONITOR__ALARM__INTERVAL=60
```

See [Configuration](docs/getting-started/configuration.md) for all variables, Telegram credential steps, and computed paths (`assets_path`, `base_path`, `logging_config`).

---

## Running

### Development

```bash
uv run main.py
```

What happens (`main.py:12`):

```python
async def main() -> None:
    settings = get_settings()
    logger = get_logger()
    pymonitor = PyMonitor(
        metric_collector=MetricsService(settings=settings, logger=logger),
        agent=PyAgent(messenger=MessengerService()),
        event_queue=asyncio.Queue(),
        database_connector=StateManager(),
    )
    await pymonitor.start()
```

`MetricsService.start()` launches 7 pollers (`asyncio.gather` on `@monitor_metric` methods). `PyAgent.start()` launches Telegram polling + active/passive monitoring. Stop with `Ctrl+C`.

### Production — Single .exe

```bash
uv sync
uv run pyinstaller --name "PyMonitor" -p ./app main.py --noconsole --onefile
# Output: dist/PyMonitor.exe
```

- Frozen `base_path` is `sys.executable` dir, so `assets/` and `app.log` must sit beside the `.exe` (`app/settings.py:97`)
- Provide `.env` beside the `.exe`
- Run **as Administrator** (right-click → Run as Administrator or Scheduled Task)
- For auto-start, create a Scheduled Task or shortcut in `shell:startup`

See [Running](docs/getting-started/running.md) for logs (`app.log` 10 MB × 5), verification (`/status`, `/photo`, alarm tests), and troubleshooting.

---

## Documentation

We use **ProperDocs** (MkDocs Material + Kroki).

```bash
uv run properdocs serve   # local preview
uv run properdocs build   # static build to site/
```

| Section | Who is it for? |
|---|---|
| [Getting Started](docs/getting-started/installation.md) | Caregivers / end-users |
| [User Guide](docs/user-guide/monitors.md) | Daily monitoring |
| [Architecture](docs/architecture/c4.md) | Developers / contributors |
| [Contributing — Adding a Monitor](docs/contributing/adding-monitor.md) | Developers |
| [Contributing — Adding an Action](docs/contributing/adding-action.md) | Developers |
| [API Reference](docs/api/core.md) | Auto-generated from Google-style docstrings |

> All diagrams are rendered via **Kroki** (Mermaid/PlantUML). Never commit raw `.png`/`.svg` — use `kroki-mermaid` or `kroki-plantuml` fences.

---

## Environment Notes

- **Windows only** — Linux/macOS development is possible, but `wmi` and `psutil.win_service_get` are mocked in tests (`tests/unit/services/test_metrics.py`). Do not run `wmic`/`powershell` on Linux CI.
- **Python 3.14+ only** — enforced in `pyproject.toml:6`
- **Logging** — `app.log` rotating (10 MB, 5 backups) + stdout/stderr (`app/settings.py:117`)

---

## Contributing

See [Project Structure](docs/contributing/structure.md) and conventions:

- Monitors: decorate with `@monitor_metric(resource_name="...", interval=60)` in `app/services/metrics.py` — must return `Event`
- Actions: add `elif resource_name == "...":` branch in `PyAgent.take_action()` (`app/services/pyagent.py`) — must be `async` and return `bool`
- Code style: `ruff check . && ruff format .`, `mypy .`, Google-style docstrings (`ruff check --select D`)
- Tests: `pytest` — `tests/unit/` mirrors `app/`; `uv run pytest` must pass

---

## License

MIT — see `pyproject.toml` for project metadata. All assets in `assets/` are bundled for alarm playback.
