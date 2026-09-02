# Roadmap

PyMonitor is evolving from a 7-monitor daemon to a full caregiver companion. Status legend: ✅ Done | 🚧 In Progress | 💡 Planned | ❌ Blocked | 🐛 Bug/Tech Debt

---

## Feature Status

| Status | Area | Feature | Description |
|---|---|---|---|
| ✅ | Core | Locked OS Monitor | Detects `LogonUI.exe` via `psutil` |
| ✅ | Core | OptiKey Monitor | Process check + auto-restart via `taskkill` |
| ✅ | Core | AnyDesk Monitor | Process check + auto-restart |
| ✅ | Core | Network Monitor | `Ethernet`/`Wi-Fi` `isup` via `net_if_stats` |
| ✅ | Core | Charger Monitor | `sensors_battery` % + plugged, status `None` if no battery |
| ✅ | Core | Tobii Hardware Monitor | `WMI Win32_PnPEntity` contains `tobii` |
| ✅ | Core | Tobii Services Monitor | 3 exes + 3 services `win_service_get`, joined message |
| ✅ | Infra | StateManager | In-memory `dict[str, Event]` deduplication, `DataBaseConnector` ABC |
| ✅ | Messaging | TelegramInterface | Polling + `/log` + `/photo` (photo_mode), `TelegramError` handling |
| ✅ | Messaging | MessengerService | Fan-out `MessageInterface` list |
| ✅ | Alerts | AlarmService | `-nok.mp3` loop + `-ok.mp3` chime for `Charger`/`Tobii_Hardware` |
| ✅ | Docs | Full rewrite | This site (ProperDocs Material, C4, sequences, dual audience) |
| 🚧 | Messaging | `/status` command | Stub at `interfaces.py:55` - should dump `StateManager.get_all()` |
| 🚧 | UX | Alarm assets | `Tobii_Hardware-ok/nok.mp3` missing from `assets/` - logs error |
| 🐛 | Core | Per-monitor `interval` ignored | Decorator `interval=60` overridden by global `check_interval=10` |
| 🐛 | Core | Poller isolation | Single poller exception kills `gather` - needs per-iteration `try/except` |
| 💡 | Core | New monitors | DiskSpace, Memory, CPU, Temperature candidates |
| 💡 | Core | Persistent state | Optional `sqlite`/`aiosqlite` `DataBaseConnector` for cross-restart history |
| 💡 | Messaging | Telegram `/restart` command | On-demand `take_action` via chat |
| 💡 | UX | Web dashboard | Local `FastAPI` + Vue for non-Telegram users |
| 💡 | Build | Auto-start service | Windows Service installer / `shell:startup` shortcut docs |
| 💡 | QA | Tests | `pytest` suite currently empty - add `StateManager` + decorator tests |

---

## Timeline

### Q3 2026 (Current)

- [x] 7 monitors + deduplication
- [x] Telegram `/log` `/photo` + polling retry (360s on `TelegramError`)
- [x] AlarmService with `playsound3` + `assets/Charger-*.mp3`
- [x] PyInstaller frozen build (`--noconsole --onefile`)
- [x] **Docs rewrite** (this release): English, dual audience, expanded nav, removed `gen_erd.py`, fixed `api/core.md` mkdocstrings
- [ ] Fix `get_status` to return `StateManager.get_all()` formatted HTML

### Q4 2026

- [ ] Ship missing `Tobii_Hardware-*.mp3` assets
- [ ] Fix per-monitor `interval` vs global `check_interval` (either respect interval or remove param)
- [ ] Add per-poller `try/except` + logging to isolate failures
- [ ] Add `pytest` coverage for `StateManager` + `@monitor_metric` dedup
- [ ] Add `DiskSpace` example monitor + action to prove contributor flow

### 2027

- [ ] Persistent `DataBaseConnector` option (sqlite)
- [ ] Telegram `/restart <resource>` on-demand remediation
- [ ] Export reports PDF for caregivers
- [ ] i18n (pt-BR toggle if requested)

---

## Contributing

Pick a `💡` or `🐛` item, implement per [Adding a Monitor](../contributing/adding-monitor.md) / [Adding an Action](../contributing/adding-action.md), and update this roadmap + monitors table in the same PR.
