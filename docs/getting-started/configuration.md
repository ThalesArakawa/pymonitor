# Configuration

PyMonitor uses **`pydantic-settings`** (`app/settings.py`) with prefix `PYMONITOR__` and nested delimiter `__`. Every setting can be set via environment variable or `.env` file (`env_file=".env"`). Secrets are **never hardcoded**.

---

## Quick Setup

```bash
cp .env.example .env
# Edit .env with your editor
notepad .env
```

Minimal `.env` for Telegram:

```ini
PYMONITOR__USE_TELEGRAM=true
PYMONITOR__TELEGRAM__BOT_TOKEN=123456:ABC-your-token-from-BotFather
PYMONITOR__TELEGRAM__CHAT_ID=987654321
PYMONITOR__USE_ALARM_SOUND=true
PYMONITOR__MONITORING__CHECK_INTERVAL=10
```

---

## All Variables (`app/settings.py`)

| Env Variable | Type | Default | Description |
|---|---|---|---|
| `PYMONITOR__ENV` | `test|dev|prod` | `test` | App environment |
| `PYMONITOR__USE_TELEGRAM` | `bool` | *required* | Enable Telegram bot |
| `PYMONITOR__TELEGRAM__BOT_TOKEN` | `str` | *required* | From [@BotFather](https://t.me/botfather) |
| `PYMONITOR__TELEGRAM__CHAT_ID` | `str` | *required* | Chat/group ID to send alerts to |
| `PYMONITOR__USE_ALARM_SOUND` | `bool` | *required* | Play audible alarms on failure |
| `PYMONITOR__ALARM__INTERVAL` | `int` | `60` | Seconds between repeating `-nok.mp3` |
| `PYMONITOR__MONITORING__CHECK_INTERVAL` | `int` | `10` | Poll interval for all monitors (overrides `@monitor_metric(interval=...)`) |
| `PYMONITOR__MONITORING__PHOTO_MODE` | `bool` | `false` | Enable `/photo` command (requires webcam) |
| `PYMONITOR__LOG_LEVEL` | `DEBUG|INFO|...` | `DEBUG` | Logging level |
| `PYMONITOR__TOBII__OPTIKEY_EXE_NAME` | `str` | `OptiKey.exe` | Process name for OptiKey |
| `PYMONITOR__TOBII__OPTIKEY_PATH` | `str` | `./OptiKey.exe` | Full path used to relaunch OptiKey |
| `PYMONITOR__TOBII__EYEX_ENGINE_EXE_NAME` | `str` | `Tobii.EyeX.Engine.exe` | Tobii EyeX Engine process |
| `PYMONITOR__TOBII__EYEX_INTERACTION_EXE_NAME` | `str` | `Tobii.EyeX.Interaction.exe` | Tobii Interaction process |
| `PYMONITOR__TOBII__SERVICE_EXE_NAME` | `str` | `Tobii.Service.exe` | Tobii Service process |
| `PYMONITOR__TOBII__SERVICE_NAME` | `str` | `Tobii Service` | Windows service name |
| `PYMONITOR__TOBII__GENERIC_NAME` | `str` | `TobiiGeneric` | Generic Tobii service |
| `PYMONITOR__TOBII__EYETRACKER_NAME` | `str` | `TobiilS5LEYETRACKER5` | Eyetracker service name |
| `PYMONITOR__REMOTE_ACCESS__ANYDESK_EXE_NAME` | `str` | `AnyDesk.exe` | AnyDesk process name |
| `PYMONITOR__REMOTE_ACCESS__ANYDESK_PATH` | `str` | `./AnyDesk.exe` | Full path used to relaunch AnyDesk |

> `PYMONITOR__LOG_FORMAT` / `PYMONITOR__LOG_DATE_FORMAT` / `PYMONITOR__LOG_LEVEL` also exist but rarely need changing. See `app/settings.py:100` computed `logging_config`.

### How nesting works

`env_nested_delimiter="__"` means `PYMONITOR__TOBII__SERVICE_NAME` maps to `settings.tobii.service_name`. `case_sensitive=False`.

---

## Getting Telegram Credentials

1. Talk to [@BotFather](https://t.me/botfather) -> `/newbot` -> copy token.
2. Start a chat with your bot, send any message.
3. Visit `https://api.telegram.org/bot<token>/getUpdates` to find `chat.id`, or use `PYMONITOR__TELEGRAM__CHAT_ID` as the group/channel ID.

---

## Computed Paths (`AppSettings`)

| Property | Value |
|---|---|
| `base_path` | `sys.executable` dir if frozen (PyInstaller), else `app/` dir |
| `assets_path` | `base_path.parent / "assets/"` - expects `Charger-ok.mp3` etc. |
| `root_path` | Project root |
| `logging_config` | `RotatingFileHandler` `app.log` 10MB x5 + stdout/stderr; silences `urllib3/httpcore/telegram/asyncio/httpx` to `INFO` |

All paths are resolved at `get_settings()` (cached).

---

## Example `.env` for Full Setup

```ini
# Telegram
PYMONITOR__USE_TELEGRAM=true
PYMONITOR__TELEGRAM__BOT_TOKEN=123:ABC
PYMONITOR__TELEGRAM__CHAT_ID=123456

# Hardware - adjust to your service names
PYMONITOR__TOBII__OPTIKEY_EXE_NAME=OptiKey.exe
PYMONITOR__TOBII__OPTIKEY_PATH=C:\OptiKey\OptiKey.exe
PYMONITOR__TOBII__SERVICE_NAME=Tobii Service
PYMONITOR__TOBII__GENERIC_NAME=TobiiGeneric
PYMONITOR__TOBII__EYETRACKER_NAME=TobiilS5LEYETRACKER5
PYMONITOR__REMOTE_ACCESS__ANYDESK_EXE_NAME=AnyDesk.exe
PYMONITOR__REMOTE_ACCESS__ANYDESK_PATH=C:\AnyDesk\AnyDesk.exe

# Behavior
PYMONITOR__MONITORING__CHECK_INTERVAL=10
PYMONITOR__MONITORING__PHOTO_MODE=true
PYMONITOR__USE_ALARM_SOUND=true
PYMONITOR__ALARM__INTERVAL=60
PYMONITOR__LOG_LEVEL=INFO
```

Next: [Running](running.md).
