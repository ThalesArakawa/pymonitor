# State & Data

PyMonitor has **no persistent database**. All state lives in an in-memory dictionary. This is intentional - the daemon is ephemeral, and Telegram + `app.log` are the audit trail.

---

## In-Memory StateManager

```kroki-plantuml
@startuml
hide circle
skinparam linetype ortho
skinparam shadowing false
skinparam roundcorner 8
skinparam DefaultFontName "Roboto"
title StateManager - In-Memory Model

entity "StateManager\napp/services/database.py" as SM {
  * state : dict[str, Event]
  --
  + update_state(key, Event)
  + get(key) -> Event
  + get_all() -> dict
}

entity "Event\napp/models/event.py" as EV {
  * event_id : str | None
  * message : str
  * resource_name : str | None
  * status : True | False | None
  * value : Any | None
  * timestamp : datetime | None
}

entity "Message\napp/models/message.py" as MSG {
  * content : str
  * type : str  // "" | "photo" | "doc"
  * byte_content : bytes | None
  * recipient : Update | None
}

entity "Request\napp/models/request.py" as REQ {
  * request_id : str | None
  * message : Any  // "log" | "photo"
  * timestamp : datetime | None
  * update : Any  // Telegram Update
}

SM ||--o{ EV : stores
EV .. MSG : becomes
REQ .. MSG : becomes via respond()

note right of EV
  status:
  True  = healthy
  False = failure
  None  = unknown (e.g., battery not present)
  value: e.g., battery percent
end note

note bottom of SM
  ABC: DataBaseConnector
  get(missing) returns Event(message="", status=None)
  => first emission always triggers
  => deduplication: only queue when
     previous.status != current.status
end note
@enduml
```

### Contract (`app/services/database.py`)

```python
class DataBaseConnector(ABC):
    def update_state(self, key: str, content: Event): ...
    def get(self, key: str) -> Event: ...
    def get_all(self) -> dict[str, Event]: ...


class StateManager(DataBaseConnector):
    def __init__(self):
        self.state = {}

    def update_state(self, key, content):
        self.state[key] = content

    def get(self, key):
        return self.state.get(key, Event(message="", status=None))

    def get_all(self):
        return self.state
```

* **Why in-memory?** PyMonitor is a single Windows process. Persistence would require file/DB I/O and migration; the current design restarts fresh on each launch and immediately re-emits the current state (because `get` miss -> `status=None` never equals `True/False`).
* **Thread safety**: Accessed only from the main `asyncio` thread (`MetricsService` and `PyAgent` share the same `StateManager` instance via `PyMonitor._initialize`), so no lock needed.
* **No `gen_erd.py`**: The `gen-files` plugin was removed from `properdocs.yml` because there is no SQLAlchemy model to introspect. If a persistent store is added later, a generator can be reintroduced.

---

## Event Lifecycle

1. **Created** by a `@monitor_metric` poller: `Event(message, status, value?)` + enriched by decorator (`event_id=uuid4`, `timestamp=utcnow`, `resource_name`).
2. **Deduplicated** against `StateManager.get(resource_name).status` - dropped if status unchanged.
3. **Queued** to `event_queue: asyncio.Queue` only on transition.
4. **Consumed** by `PyAgent.active_monitoring`: `take_action` + `MessengerService.send(Message(content=Event.message))` + `AlarmService.send_alarm(Event)`.
5. **State updated** before queuing, so subsequent polls compare against the new baseline.

### Example Events

| Monitor | `resource_name` | `status` | `value` | `message` excerpt |
|---|---|---|---|---|
| `charger_status` | `Charger` | `True` / `False` / `None` | `85` (%) | `Charger is connected (85%)` |
| `network_status` | `Network` | `True`/`False` | - | `Network is UP` |
| `check_tobii_status` | `Tobii_Services` | `True`/`False` | - | `Tobii.EyeX.Engine.exe is UP\n...` (joined 6 lines) |

---

## Future Considerations

* **Persistence** (optional): If alert history across restarts is needed, replace `StateManager` with a `sqlite` + `aiosqlite` implementation of `DataBaseConnector` without changing `MetricsService`/`PyAgent` (they depend only on the ABC).
* **Testing**: `StateManager` is trivially mockable; integration tests can inject a fake `DataBaseConnector` to assert deduplication.

See [Adding a Monitor](../contributing/adding-monitor.md) for how the `Event` contract is used.
