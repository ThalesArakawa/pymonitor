# PyMonitor

> **Windows companion for ALS users** - Keep OptiKey, Tobii Eye Tracker, AnyDesk and essential hardware alive. Notify caregivers instantly via Telegram.

PyMonitor is an open-source, Windows-only monitoring daemon built for people with ALS who rely on assistive technologies like **OptiKey** and **Tobii** eye-trackers. It runs in the background, polls system health every few seconds, and - only when something changes - sends an HTML message to Telegram and plays an audible alarm.

---

## What it Does

| Capability | Details |
|---|---|
| **7 Monitors** | Locked OS, OptiKey, AnyDesk, Network, Charger/Battery, Tobii Hardware, Tobii Services |
| **Auto-Remediation** | Restarts Tobii services (`sc stop/start`), OptiKey and AnyDesk processes (`taskkill` + relaunch) - requires Administrator |
| **Telegram Bot** | Commands `/status`, `/log`, `/photo` (optional webcam snapshot) |
| **Alarms** | Repeating `Charger-nok.mp3` / `Tobii_Hardware` sounds via `playsound3` until the issue clears, then a success chime |
| **In-Memory State** | `StateManager` deduplicates - you only get notified on transitions (`True` <-> `False`) |

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

CG -> TG : /log /photo
TG -> PA : Bot API polling
MS -> SM : Event deduplication
MS -> PA : EventQueue
PA -> TG : HTML messages
PA -> CG : PyMonitor response
PA -> AL : audible alerts
@enduml
```

See [Architecture Overview](architecture/c4.md) for full C4 diagrams.

## Quick Start

```bash
# 1. Install deps (Python 3.14+ required)
uv sync

# 2. Configure — copy and fill secrets
cp .env.example .env
# Edit .env: PYMONITOR__USE_TELEGRAM, PYMONITOR__TELEGRAM__BOT_TOKEN, PYMONITOR__TELEGRAM__CHAT_ID

# 3. Run
uv run main.py

# 4. Preview docs
uv run properdocs serve
```

> **Windows only.** Requires Administrator privileges for service restarts. See [Installation](getting-started/installation.md).

## Choose Your Path

<div class="grid cards" markdown>

-   :material-download: **I want to install PyMonitor**

    ---

    For caregivers and end-users. Follow the step-by-step install and configuration.

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

-   :material-code-tags: **I want to contribute**

    ---

    For developers adding monitors or remediation actions.

    [:octicons-arrow-right-24: Project Structure](contributing/structure.md)

-   :material-book-open-page-variant: **I want to understand the system**

    ---

    C4 diagrams, sequence flows, and state design.

    [:octicons-arrow-right-24: Architecture](architecture/c4.md)

-   :material-api: **I want the API**

    ---

    Auto-generated reference from docstrings for every service and model.

    [:octicons-arrow-right-24: API Reference](api/core.md)

</div>

## Requirements

* **OS**: Windows 10/11 (uses `wmi`, `psutil.win_service_get`, `sc`, `taskkill`)
* **Python**: 3.14+
* **Telegram Bot**: Token + Chat ID from [@BotFather](https://t.me/botfather) (optional but recommended)
* **Hardware**: Tobii Eye Tracker (optional), webcam (optional for `/photo`)

## Documentation Map

| Section | Who is it for? |
|---|---|
| [Getting Started](getting-started/installation.md) | End-users / caregivers |
| [User Guide](user-guide/monitors.md) | End-users monitoring daily status |
| [Architecture](architecture/c4.md) | Both - understand the system |
| [Contributing](contributing/adding-monitor.md) | Developers |
| [Roadmap](dev/roadmap.md) | Both - what's next |
| [API Reference](api/core.md) | Developers |

---

!!! tip "First time?"
    Start with [Installation](getting-started/installation.md) -> [Configuration](getting-started/configuration.md) -> [Telegram Commands](user-guide/telegram.md).
