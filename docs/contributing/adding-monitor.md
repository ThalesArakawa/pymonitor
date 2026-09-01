# Adding a Monitor

Follow this recipe to add a new health check. The pattern is enforced by `AGENTS.md` and `app/services/metrics.py:7`.

---

## Steps

### 1. Add a method to `MetricsService` (`app/services/metrics.py`)

```python
from ..models import Event
from .log import get_logger
from .metrics import monitor_metric  # the decorator


class MetricsService:
    # ... existing 7 monitors ...

    @monitor_metric(resource_name="MyResource", interval=60)
    async def myresource_status(self) -> Event:
        # --- your polling logic ---
        # e.g. check a file, service, or hardware
        is_ok = await self._check_something()  # or sync psutil/wmi

        if is_ok:
            return Event(message="MyResource is UP", status=True, value=None)
        else:
            return Event(message="MyResource is DOWN", status=False, value=None)
```

**Requirements**:

* Decorate with `@monitor_metric(resource_name="[NAME]", interval=[SECONDS])`.
* Must return an `Event` with `(message, status, value?)` (`app/models/event.py`).
* `resource_name` is the deduplication key used by `StateManager` - choose a stable string.
* `interval` overrides `settings.monitoring.check_interval` per-monitor (fallback to global).

### 2. The Decorator Does the Rest

```python
def monitor_metric(resource_name, interval=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            while True:
                await _collect_and_emit(...)  # handles status diff + queue
                await asyncio.sleep(_resolve_interval(interval, settings.check_interval))

        wrapper._is_monitor = True
        return wrapper
```

* Enriches `Event` with `event_id`, `timestamp`, `resource_name`.
* Deduplicates via `StateManager.get(resource_name).status` - only queues on flip. Return `status=None` for "unknown" (e.g. no battery).
* Registers via `_setup()` (`metrics.py:30`): `inspect.getmembers(self, predicate=ismethod where _is_monitor)`.

**No manual `start()` call needed** - `MetricsService._setup()` auto-discovers decorated methods at `__init__`.

### 3. Update Docs

Per `AGENTS.md:48`:

* Add a row to [User Guide Monitors](../user-guide/monitors.md) table.
* Add an entry to [Roadmap](../dev/roadmap.md) if needed.

### 4. Test

```bash
uv run python -c "from app.services.metrics import MetricsService; m=MetricsService(); print(m.valid_methods)"
# Should list your new method

uv run main.py  # Watch app.log for your resource_name appearing
```

Run `uv run properdocs serve` to verify docs render.

---

## Example: Disk Space Monitor

```python
import shutil


@monitor_metric(resource_name="DiskSpace", interval=60)
async def disk_space_status(self) -> Event:
    usage = shutil.disk_usage("/")
    percent_free = (usage.free / usage.total) * 100
    if percent_free > 10:
        return Event(
            message=f"Disk OK ({percent_free:.1f}% free)",
            status=True,
            value=percent_free,
        )
    else:
        return Event(
            message=f"Disk LOW ({percent_free:.1f}% free)",
            status=False,
            value=percent_free,
        )
```

* `value` can carry the free percent for downstream use (logging, future Telegram formatting).
* Use `psutil`/`wmi` for Windows-specific checks; keep them synchronous for now.

---

## Pitfalls

* **Returning wrong type**: Must be `Event`, not `bool` or `str`. Pydantic will validate (`Event.validate_assignment`).
* **Forgetting `resource_name`**: Decoration key must match the string you check in `PyAgent.take_action` if you add remediation.
* **Blocking calls**: Long `wmi` queries block the event loop - wrap in `asyncio.to_thread` if needed (see `pyagent.py:restart_tobii_service` pattern).
* **Linux paths**: Don't add `systemd` or `/proc` checks - project is Windows-only by design.
