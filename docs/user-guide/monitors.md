# Monitors

PyMonitor ships with **7 built-in monitors** (`app/services/metrics.py`). Each polls via `@monitor_metric(resource_name, interval=60)` and sleeps `interval` if set, otherwise `settings.monitoring.check_interval` (default **10s**). An `Event` is only emitted when `status` flips, so you won't get spammed.

> For developers adding a monitor, see [Adding a Monitor](../contributing/adding-monitor.md).

---

## Overview

| Resource | What it checks | Healthy (`True`) | Failed (`False`) | Unknown (`None`) |
|---|---|---|---|---|
| **Locked OS** | `LogonUI.exe` present via `psutil` | OS unlocked | OS locked (login screen) | - |
| **Optikey** | Process `optikey_exe_name` running | `OptiKey.exe` found | Not found | - |
| **AnyDesk** | Process `anydesk_exe_name` running | `AnyDesk.exe` found | Not found | - |
| **Network** | `psutil.net_if_stats()` for `Ethernet`/`Wi-Fi` `isup` | Either UP | Both DOWN | - |
| **Charger** | `psutil.sensors_battery()` | `power_plugged == True` | `False` (on battery) | `battery is None` (no battery) |
| **Tobii_Hardware** | `wmi.WMI().Win32_PnPEntity()` Name contains `tobii` case-insensitive | Found | Not found | - |
| **Tobii_Services** | 3 exes + 3 `win_service_get` statuses | All 6 UP | Any DOWN | - |

Each monitor returns `Event(message, status, value?)` where `value` is e.g. battery percent (see below). The decorator enriches with `event_id` (uuid4), `timestamp`, `resource_name`.

---

## Details

### Locked OS (`locked_status`)
```python
@monitor_metric(resource_name="Locked OS", interval=60)
async def locked_status(self) -> Event:
```
Scans `psutil.process_iter()` for `LogonUI.exe`. If found, OS is locked. Useful to know if the user was logged out.

### Optikey (`optikey_status`)
Checks `proc.name() == settings.tobii.optikey_exe_name`. Auto-remediated by `PyAgent.restart_optikey` (`taskkill` + relaunch at `optikey_path`). Config via `PYMONITOR__TOBII__OPTIKEY_*`.

### AnyDesk (`anydesk_status`)
Checks `proc.name() == settings.remote_access.anydesk_exe_name`. Auto-remediated by `restart_anydesk`. Config via `PYMONITOR__REMOTE_ACCESS_*`.

### Network (`network_status`)
```python
stats = psutil.net_if_stats()
# checks stats.get("Ethernet") and stats.get("Wi-Fi")
```
If either interface `isup` -> healthy. Reports which interface is up/down in the message.

### Charger (`charger_status`)
```python
b = psutil.sensors_battery()
# b is None -> status None, message "Battery not available"
# else power_plugged + percent
```
On desktop without battery, you'll always see `None` and no alarm. On laptop, triggers audible alarm via `AlarmService`.

* `value` = `percent` (e.g. `87`).
* Alarms: yes (`Charger` is in `AlarmService` allowlist).

### Tobii Hardware (`tobii_hardware_status`)
```python
wmi.WMI().Win32_PnPEntity()
# any entity where "tobii" in entity.Name.lower()
```
Detects USB eyetracker presence. Alarms: yes. Resource name is `"Tobii_Hardware"`.

### Tobii Services (`check_tobii_status`)
Most complex. Checks **6** things and joins results with `\n`:

* Processes: `eyex_engine_exe_name`, `eyex_interaction_exe_name`, `service_exe_name` via `psutil.process_iter()`.
* Services: `service_name`, `generic_name`, `eyetracker_name` via `psutil.win_service_get(service).status()`.

If all 6 are `running`/`UP` -> `status=True`, else `False`. Message lists each as `UP`/`DOWN`. Auto-remediated by `restart_tobii_service` (`sc stop/start` for 3 services).

---

## Event Deduplication

```python
# Inside @monitor_metric wrapper (app/services/metrics.py)
previous = self.state_tracker.get(resource_name)  # miss -> Event(status=None)
if previous.status != current.status:
    self.state_tracker.update_state(resource_name, current)
    await self.event_queue.put(current)
await asyncio.sleep(settings.monitoring.check_interval)
```

* First emission for a resource always fires (because `None != True/False`).
* You only get a Telegram message + alarm on **transition**. Polluting every 10s is prevented.
* State is in-memory (`StateManager` dict), reset on restart.

---

## Tuning

* `PYMONITOR__MONITORING__CHECK_INTERVAL=10` is the fallback; `interval=60` in the decorator overrides it per-monitor.
* Add `PYMONITOR__LOG_LEVEL=DEBUG` to see each poll in `app.log`/`stdout`.

---

## Next: [Telegram Commands](telegram.md) | [Alarms](alarms.md)
