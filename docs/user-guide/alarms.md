# Alarms

Audible alerts ensure a caregiver **in the room** notices a failure even without looking at Telegram. Currently active for `Charger` and `Tobii_Hardware` only.

---

## How It Works (`app/services/alarm.py`)

```python
class AlarmService:
    alarm_state: dict[str, asyncio.Event] = {}
    tasks: dict[str, asyncio.Task] = {}
```

* `PyAgent.active_monitoring` calls `alarm_service.send_alarm(Event)` in parallel with `messenger.send` for every status flip.
* `send_alarm` filters to `["Charger", "Tobii_Hardware"]` - other resources never sound.
* `play_alarm(Event)` branches:

| `Event.status` | Action |
|---|---|
| `False` (failure) | Cancel any existing stop-event, create `asyncio.Event` + `Task(on_failure)` |
| `True` (recovered) | `set()` the Event to stop the loop, then `on_success()` plays the chime once |
| `None` | No-op |

### Failure Loop (`on_failure`)

```python
async def on_failure(self, audio: Path, resource_name: str):
    while not self.alarm_state[resource_name].is_set():
        await asyncio.to_thread(playsound3.playsound, str(audio), False)
        try:
            await asyncio.wait_for(self.alarm_state[resource_name].wait(), timeout=self.settings.alarm.interval)
        except asyncio.TimeoutError:
            continue  # replay
```

* Audio file: `settings.assets_path / f"{resource_name}-nok.mp3"` (e.g. `Charger-nok.mp3`).
* Uses `playsound3.playsound(..., False)` in `to_thread` to not block the event loop.
* Repeats every `alarm.interval` (default 60s, `PYMONITOR__ALARM__INTERVAL`) until `Event(status=True)` sets the `asyncio.Event`.
* Logs `Alarm task for resource {name} started/stopped`.

### Success Chime (`on_success`)

```python
async def on_success(self, audio: Path, resource_name: str):
    audio = assets_path / f"{resource_name}-ok.mp3"
    await asyncio.to_thread(playsound3.playsound, str(audio), False)
```

Played **once** when the resource recovers. E.g. charger reconnected -> `Charger-ok.mp3`.

---

## Assets

Located at `settings.assets_path` (`base_path.parent / "assets/"`):

```
assets/
  Charger-ok.mp3   (42k) - success
  Charger-nok.mp3  (46k) - failure loop
  # Tobii_Hardware-ok.mp3 and -nok.mp3 expected but not shipped - will log "does not exist"
```

* Check `is_file()` before playing; missing file logs `"Alarm for {resource} does not exist."` and no sound plays.
* When building with PyInstaller, copy `assets/` next to the `.exe`.

---

## Configuration

```ini
PYMONITOR__USE_ALARM_SOUND=true     # master switch (required bool)
PYMONITOR__ALARM__INTERVAL=60       # seconds between repeats, >0 validated
```

If `USE_ALARM_SOUND` is `false`, `AlarmService` is still instantiated but `send_alarm` will still be called - the service itself doesn't gate on this flag (future improvement, see Roadmap).

---

## User Perspective

| Scenario | Telegram | Sound |
|---|---|---|
| Charger unplugged | `Charger is not connected (67%)` | `Charger-nok.mp3` every 60s |
| Charger plugged back | `Charger is connected (68%)` | `Charger-ok.mp3` once, loop stops |
| Tobii hardware unplugged | `Tobii Hardware is DOWN` | `Tobii_Hardware-nok.mp3` loop (if file present) |
| AnyDesk crash | `AnyDesk is DOWN` | No sound (not in allowlist) |
| Network down | `Network is DOWN` | No sound |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No sound on failure | `USE_ALARM_SOUND` not relevant? File missing? | Check `assets/Charger-nok.mp3` exists at `assets_path`; see logs |
| Loop never stops | Recovery `Event(status=True)` never emitted | Check monitor is polling; `check_tobii_status` may be stuck on WMI |
| Overlapping alarms | Two resources failing simultaneously | `tasks` dict is per-`resource_name`, so they play concurrently (one `Task` each) |

See [Monitors](monitors.md) for which resources exist, and [Configuration](../getting-started/configuration.md) for `ALARM__INTERVAL`.
