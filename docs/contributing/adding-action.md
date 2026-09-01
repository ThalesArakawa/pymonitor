# Adding a Remediation Action

Remediation actions are strategy branches inside `PyAgent.take_action()` (`app/services/pyagent.py`). They attempt to self-heal before notifying.

---

## Steps

### 1. Add a branch in `PyAgent.take_action` (`app/services/pyagent.py`)

```python
class PyAgent:
    async def take_action(self, event: Event) -> bool | None:
        resource_name = event.resource_name
        if resource_name == "Tobii_Services":
            return await asyncio.to_thread(self.restart_tobii_service, event)
        elif resource_name == "Optikey":
            return await self.restart_optikey(event)
        elif resource_name == "AnyDesk":
            return await self.restart_anydesk(event)
        elif resource_name == "DiskSpace":  # <-- your new resource
            return await self.restart_disk_cleanup(event)
        else:
            return None  # no remediation for this resource
```

**Requirement**: Must implement an `async` method returning `bool` (success/fail) or `None` if no action applies.

### 2. Implement the `async` method

Follow existing patterns:

#### Pattern A: Windows service restart (`restart_tobii_service`)

```python
def restart_tobii_service(self, event: Event) -> bool:
    # Synchronous, called via to_thread from take_action
    for svc in [self.settings.tobii.service_name,
                self.settings.tobii.generic_name,
                self.settings.tobii.eyetracker_name]:
        subprocess.run(["sc", "stop", svc], creationflags=CREATE_NO_WINDOW)
        subprocess.run(["sc", "start", svc], creationflags=CREATE_NO_WINDOW)
    return True  # or check returncodes
```

* Uses `sc stop/start` + `CREATE_NO_WINDOW` to avoid flashing console.
* Called via `asyncio.to_thread` because it's blocking.

#### Pattern B: Process kill + relaunch (`restart_optikey`, `restart_anydesk`)

```python
async def restart_optikey(self, event: Event) -> bool:
    exe = self.settings.tobii.optikey_exe_name
    path = Path(self.settings.tobii.optikey_path)
    if not path.is_file():
        self.logger.error(f"OptiKey path not found: {path}")
        return False
    # Kill
    subprocess.run(["taskkill", "-f", "-im", exe], creationflags=CREATE_NO_WINDOW)
    await asyncio.sleep(1)
    # Relaunch
    await asyncio.create_subprocess_exec(str(path), creationflags=CREATE_NO_WINDOW)
    return True
```

* `taskkill -f -im <exe>` + `create_subprocess_exec(path)`.
* Check `Path.is_file()` first; log and return `False` if missing.
* Requires **Administrator** - document this.

#### Pattern C: Your custom logic

```python
async def restart_disk_cleanup(self, event: Event) -> bool:
    try:
        # e.g., clean temp files, restart a service, etc.
        await asyncio.to_thread(self._do_cleanup)
        self.logger.info("DiskSpace remediation succeeded")
        return True
    except Exception as e:
        self.logger.error(f"DiskSpace remediation failed: {e}")
        return False
```

* Always return `bool`; callers use it for logging but not for retry (yet).
* Log at `INFO` on success, `ERROR` on failure.

### 3. Update Docs

Per `AGENTS.md:48`:

* Document the new `elif` branch in this file's table or in [Roadmap](../dev/roadmap.md).
* Add remediation note to [User Guide Monitors](../user-guide/monitors.md) for that resource.

### 4. Test

```bash
# Manual: force a failure Event
uv run python -c "
import asyncio
from app.services.pyagent import PyAgent
from app.services.messenger import MessengerService
from app.models.event import Event

async def test():
    agent = PyAgent(MessengerService())
    ev = Event(message='test', status=False, resource_name='DiskSpace')
    result = await agent.take_action(ev)
    print(result)

asyncio.run(test())
"
```

Check `app.log` for your log lines, and verify `needs Admin` not violated.

---

## Design Notes

* `take_action` runs inside `active_monitoring` (`pyagent.py:130`) concurrently with `messenger.send` + `alarm.send_alarm` via `asyncio.gather`.
* A `False` return does **not** requeue the `Event` - the failure is still notified via Telegram/Alarm regardless of remediation success.
* For long-running remediation, prefer `asyncio.to_thread` to avoid blocking the queue consumer.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Action never called | `resource_name` string mismatch - must equal `@monitor_metric(resource_name=...)` exactly |
| `taskkill` fails | Not Administrator; or exe name wrong (`PYMONITOR__TOBII__*` typo) |
| `path not found` | `PYMONITOR__TOBII__OPTIKEY_PATH` not set or relative to wrong `base_path` (frozen vs dev) |
| `CREATE_NO_WINDOW` undefined | Import from `subprocess` - already done in `pyagent.py` |
