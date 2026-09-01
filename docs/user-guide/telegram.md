# Telegram Commands

PyMonitor uses **Telegram** as its primary caregiver interface (`python-telegram-bot 22.6`). All messages are HTML-formatted and sent to `PYMONITOR__TELEGRAM__CHAT_ID`.

Enable it:

```ini
PYMONITOR__USE_TELEGRAM=true
PYMONITOR__TELEGRAM__BOT_TOKEN=123:ABC-from-BotFather
PYMONITOR__TELEGRAM__CHAT_ID=987654321
```

If `USE_TELEGRAM=false`, `get_interfaces()` returns an empty list and no polling occurs.

---

## Alerts (Automatic)

Whenever a monitor flips (`True` <-> `False`), you get:

```
⚠️ Tobii_Services
Tobii.EyeX.Engine.exe is DOWN
Tobii.EyeX.Interaction.exe is UP
Tobii Service is DOWN
...
```

Sent via `TelegramInterface.send` -> `bot.send_message(chat_id, text, parse_mode="HTML")` (`app/services/interfaces.py:93`). Failures are logged as `Telegram error: {e}` (`TelegramError` base).

---

## Commands (On-Demand)

Send these in the Telegram chat with your bot:

| Command | Handler | `photo_mode` required? | What it does |
|---|---|---|---|
| `/status` | `get_status` (`interfaces.py:55`) | No | **Currently stub** - logs `DEBUG` only, no reply. See Roadmap. |
| `/log` | `get_log` (`interfaces.py:58`) | No | Returns `app.log` as `application_log.txt` document |
| `/photo` | `get_photo` (`interfaces.py:69`) | **Yes** | Returns webcam JPEG snapshot |

### `/log`

* Enqueues `Request(message="log", update=Update)` to `request_queue`.
* `PyAgent.passive_monitoring` -> `respond` -> `get_log()` (`aiofiles.open(base_path/app.log, "rb").read()`) -> `Message(type="doc", byte_content=bytes, recipient=Update)` -> `reply_document(BytesIO, "application_log.txt")` (`app/services/pyagent.py:35`, `app/services/interfaces.py:87`).

Works even with large logs (reads fully into memory; `app.log` rotates at 10MB).

### `/photo`

* Requires `PYMONITOR__MONITORING__PHOTO_MODE=true` (`app/services/interfaces.py:42` conditional handler). If `false`, the handler is not registered and the bot ignores `/photo`.
* Captures via `cv2.VideoCapture(0)` -> `imencode .jpeg` -> `reply_photo` (`app/services/pyagent.py:25`, `app/services/interfaces.py:84`).
* If webcam missing, `get_photo()` returns `None` and the `Message` will carry `None` bytes (logged).

### `/status`

* Placeholder. Currently only `logger.debug("Getting Status")`. A future implementation could dump `StateManager.get_all()`.

---

## Technical Flow

```
[Telegram App] --/log--> [Bot API] --polling--> [TelegramInterface.listen]
  -> CommandHandler("log", get_log) -> request_queue.put(Request)
    -> [PyAgent.passive_monitoring] -> respond() -> MessengerService.send -> reply_document
```

`listen()` (`app/services/interfaces.py:38`):

```python
while not self.connected:
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        self.connected = True
    except TelegramError as e:
        logger.error(f"Failed to connect to Telegram {e}")
        await asyncio.sleep(360)  # retry 6 min
```

Catches `TelegramError` (base for `NetworkError`, `InvalidToken`, `Conflict`, etc.), not generic `Exception`.

---

## Getting Your Credentials

1. Message [@BotFather](https://t.me/botfather): `/newbot` -> choose name -> copy `bot_token`.
2. Start a chat with the bot, send any message.
3. `curl https://api.telegram.org/bot<token>/getUpdates` -> find `message.chat.id`.
4. For groups, add the bot to the group and use the group's `chat.id`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Bot ignores commands | Check `photo_mode` for `/photo`; verify `USE_TELEGRAM=true` and polling connected (`app.log` says `Starting to listen to Telegram Interface`) |
| `Invalid token` in logs | Token has whitespace/quotes -> strip in `.env` (no quotes needed) |
| `/log` returns empty | `app.log` path is `base_path.parent / "app.log"` - ensure file exists beside exe |
| Spam on every poll | Should not happen; state dedup at `metrics.py` prevents it. Check `StateManager` is shared instance |

Next: [Alarms](alarms.md) or [Adding an Action](../contributing/adding-action.md) (dev).
