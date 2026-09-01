# PyMonitor - OpenCode Context

## Setup & Commands
Use `uv` for all dependency management and execution.
- **Install/Sync**: `uv sync`
- **Run**: `uv run main.py`
- **Test**: `pytest`
- **Lint & Format**: `ruff check . && ruff format .`
- **Typecheck**: `mypy .`
- **Build (Windows)**: `uv run pyinstaller --name "PyMonitor" -p .\app\ main.py --noconsole --onefile`

## Project Context
PyMonitor is an open-source tool designed for individuals with ALS, supporting Optikey and Tobii hardware. It is a Windows-only application that requires Python 3.14+.

## Architecture & Core Components
- **Entry Point**: `main.py` -> `app.services.pymonitor.PyMonitor`
- **Configuration**: Managed via `app/settings.py` (using `pydantic-settings`). All variables use the `PYMONITOR__` prefix.
- **Async Core**: `asyncio` runs `MetricsService` (monitoring) and `PyAgent` (actions/Telegram).
- **State Management**: In-memory `StateManager` implementing the `DataBaseConnector` ABC.
- **Windows Integration**: Heavily uses `wmi`, `psutil`, Windows service APIs, and `sc`/`taskkill` commands. Requires Administrator privileges for service restart actions.

## Development Workflows

### 1. Adding a New Monitor
Add the method to `app/services/metrics.py`.
Decorate it with `@monitor_metric(resource_name="[NAME]", interval=[SECONDS])`.
**Requirement**: Must return an `Event` object with `(message, status, value?)`.

### 2. Adding a Remediation Action
Add a new `elif resource_name == "[NAME]":` branch inside `PyAgent.take_action()` in `app/services/pyagent.py`.
**Requirement**: Must implement an `async` method returning a `bool` (success/fail status).

## Environment Variables
NEVER hardcode secrets or API keys. Read all settings from environment variables.
Required `.env` setup:
- `PYMONITOR__USE_TELEGRAM`: Enable/disable Telegram bot.
- `PYMONITOR__TELEGRAM__BOT_TOKEN` & `PYMONITOR__TELEGRAM__CHAT_ID`: Bot credentials.
- `PYMONITOR__TOBII__*`: Tobii eyetracker service/executable names.
- `PYMONITOR__REMOTE_ACCESS__ANYDESK_*`: AnyDesk path/executable.
- `PYMONITOR__MONITORING__CHECK_INTERVAL`: Polling interval in seconds.
- `PYMONITOR__USE_ALARM_SOUND`: Toggle sound on alerts.

## Critical Constraints & Gotchas
- **Python 3.14+ Only**: Ensure all code is compatible with 3.14+.
- **Windows Exclusivity**: Do not suggest Linux/macOS alternatives (e.g., `systemd`).
- **Logging**: Writes to `app.log` (10MB rotating, 5 backups). Do not change to console-only logging.
- **Assets**: Alarm sounds reside in the `assets/` directory.

## Documentation
- **Engine:** ProperDocs (`uv run properdocs serve` / `uv run properdocs build`)
- **Skill Trigger:** Whenever you write code comments, modify `MetricsService`, update `PyAgent`, or touch the `docs/` folder, you MUST read and follow the `.claude/skills/python-docs/SKILL.md` ruleset.