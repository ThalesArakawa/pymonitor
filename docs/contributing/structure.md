# Project Structure

---

## Layout

```
pymonitor/
├── main.py                     # Entry point -> PyMonitor
├── app/
│   ├── settings.py             # pydantic-settings, PYMONITOR__ prefix
│   ├── models/
│   │   ├── event.py            # Event(message, status, value, timestamp)
│   │   ├── message.py          # Message(content, type, byte_content, recipient)
│   │   └── request.py          # Request(message, timestamp, update)
│   └── services/
│       ├── pymonitor.py        # Orchestrator: wires Queues + StateManager
│       ├── metrics.py          # MetricsService + @monitor_metric (7 pollers)
│       ├── pyagent.py          # PyAgent: active/passive, take_action, restart_*
│       ├── messenger.py        # MessengerService + get_interfaces()
│       ├── interfaces.py       # MessageInterface, TelegramInterface
│       ├── alarm.py            # AlarmService (per-resource Events + Tasks)
│       ├── database.py         # DataBaseConnector ABC + StateManager (dict)
│       └── log.py              # get_logger() (RotatingFileHandler)
├── assets/
│   ├── Charger-ok.mp3
│   └── Charger-nok.mp3
├── docs/                       # This site (ProperDocs / Material)
├── properdocs.yml              # Site config (theme, plugins, nav)
├── pyproject.toml              # Deps, requires-python >=3.14
└── app.log                     # Runtime log (10MB rotate, 5 backups)
```

## Wiring (`main.py` -> `app/services/pymonitor.py`)

```python
# main.py
settings = get_settings()
event_queue = asyncio.Queue()
state = StateManager()
metrics = MetricsService()            # 7 infinite pollers
messenger = MessengerService()        # -> TelegramInterface if USE_TELEGRAM
agent = PyAgent(messenger)            # queues + alarm
monitor = PyMonitor(metrics, agent, event_queue, state)
await monitor.start()                 # gather(metrics.start(), agent.start())
```

`PyMonitor._initialize()` (`app/services/pymonitor.py:10`):

```python
self.metric_collector.set_event_queue(event_queue)
self.metric_collector.set_state_tracker(database_connector)
self.agent.set_event_queue(event_queue)
self.agent.set_state_tracker(database_connector)
self.agent.messenger_service.initialize(queue=agent.request_queue)
self.tasks.append(create_task(metric_collector.start()))
self.tasks.append(create_task(agent.start()))
```

## Service Dependencies

```
MetricsService --Event--> event_queue --Event--> PyAgent.active_monitoring
TelegramInterface --Request--> request_queue --Request--> PyAgent.passive_monitoring
PyAgent --Message--> MessengerService --Message--> TelegramInterface.send
PyAgent --Event--> AlarmService
MetricsService <-> StateManager (get/update_state)
PyAgent <-> StateManager (reads state if needed)
All -> Settings (get_settings() cached)
All -> Logger (get_logger() "pymonitor")
```

## Key Abstractions

| Abstraction | File | Purpose |
|---|---|---|
| `DataBaseConnector` ABC | `database.py:5` | `update_state`, `get`, `get_all` - swappable for persistent store |
| `StateManager` | `database.py:15` | `dict[str, Event]` impl; `get` miss -> `Event(status=None)` forces first emit |
| `MessageInterface` ABC | `interfaces.py:15` | `send(Message) -> bool` - Telegram today, extensible |
| `Event` | `models/event.py:5` | `status: True|False|None`, `value: Any`, Pydantic validated |
| `monitor_metric` decorator | `metrics.py:7` | Enrich + diff + queue + sleep wrapper for pollers |

## Adding Code

* **New monitor**: See [Adding a Monitor](adding-monitor.md) - method in `metrics.py`.
* **New action**: See [Adding an Action](adding-action.md) - branch in `pyagent.py:take_action`.
* **New interface**: Implement `MessageInterface`, register in `get_interfaces()`, update `messenger.py` and docs.

## Important Notes

* **Windows-only**: `wmi`, `psutil.win_service_get`, `sc`, `taskkill` have no Linux fallback. Don't add `systemd` paths.
* **Async**: All monitors are `async def` but do blocking `psutil`/`wmi` calls synchronously. Future improvement is `to_thread`.
* **State sharing**: Single `StateManager` instance passed to both `MetricsService` and `PyAgent` - not two dicts.
* **Queues**: `event_queue` (Metrics->Agent) and `request_queue` (Telegram->Agent) are separate `asyncio.Queue` instances.
