# Running

---

## Development Mode

```bash
# From project root, Administrator terminal
uv run main.py
```

What happens (`main.py:8`):

```python
async def main():
    settings = get_settings()          # pydantic-settings from .env
    logger = get_logger()              # RotatingFileHandler app.log
    event_queue = asyncio.Queue()
    # Wiring
    metrics = MetricsService()
    messenger = MessengerService()
    agent = PyAgent(messenger)
    state = StateManager()
    monitor = PyMonitor(metrics, agent, event_queue, state)
    await monitor.start()              # gather( metrics.start(), agent.start() )
```

* `MetricsService.start()` launches 7 pollers (`gather` on `@monitor_metric` methods).
* `PyAgent.start()` launches `messenger.start()` (Telegram polling) + `active_monitoring` + `passive_monitoring`.

Stop with `Ctrl+C`.

### Preview Docs

```bash
uv run properdocs serve
# http://127.0.0.1:8000
```

---

## Production - Single .exe (Windows)

```bash
uv sync
uv run pyinstaller --name "PyMonitor" -p .\app\ main.py --noconsole --onefile
# Output: dist/PyMonitor.exe
```

PyInstaller details (`app/settings.py:90`):

* Frozen `base_path` = `sys.executable` dir, so `assets/` and `app.log` are resolved relative to the exe.
* Copy `assets/` next to the exe, and provide `.env` beside it.
* Run **as Administrator** (right-click -> Run as Administrator or set in shortcut properties).

To auto-start on boot, create a scheduled task or place a shortcut in `shell:startup`.

---

## Logs

* **File**: `app.log` beside `main.py` (dev) or beside `.exe` (frozen). Rotates at 10MB, keeps 5 backups (`app/settings.py:105`).
* **Levels**: Controlled by `PYMONITOR__LOG_LEVEL` (default `DEBUG`). Libraries `urllib3/httpcore/telegram/asyncio/httpx` silenced to `INFO`.
* **Via Telegram**: `/log` returns the file as `application_log.txt` (`aiofiles`).

Check health:

```powershell
type app.log | Select-Object -Last 20
# or
uv run python -c "from app.services.log import get_logger; print(get_logger().handlers)"
```

---

## Verifying

1. **Telegram**: Send `/status` to your bot (currently logs only, see Roadmap), `/log` should return a document, `/photo` (if `photo_mode=true`) should return a JPEG.
2. **Alarms**: Unplug charger or stop a Tobii service (`sc stop "Tobii Service"`) - Telegram alert + repeating sound until you fix it.
3. **Processes**: `tasklist | findstr OptiKey` - killing the process should trigger auto-restart within one `check_interval`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Invalid token` | `BOT_TOKEN` wrong | Re-copy from BotFather, no quotes in `.env` |
| Bot not responding | `USE_TELEGRAM=false` or `CHAT_ID` wrong | Set `true` + correct ID; check `getUpdates` |
| No auto-restart | Not Administrator | Run as Administrator |
| `/photo` does nothing | `photo_mode=false` | Set `PYMONITOR__MONITORING__PHOTO_MODE=true` |
| Alarm loops forever | `*.mp3` missing | Ensure `assets/Charger-nok.mp3` exists beside exe; check logs |
| `wmi` import error | Not Windows | PyMonitor is Windows-only by design |
