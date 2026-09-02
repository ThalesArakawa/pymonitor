# Conventions

Development rules extracted from `AGENTS.md` and codebase.

---

## General

* **Python**: 3.14+ (`pyproject.toml:6`, `.python-version`). Use 3.14 features (e.g. `type` aliases) freely.
* **Package manager**: `uv` only (`uv sync`, `uv run`, `uv run properdocs`). Don't use `pip` directly.
* **OS**: Windows-only. Uses `wmi`, `psutil.win_service_get`, `sc`, `taskkill`, `CREATE_NO_WINDOW`. Don't propose `systemd`/Linux alternatives.
* **Async**: Core is `asyncio` (`MetricsService` pollers + `PyAgent` consumers). New I/O should be `async` or offloaded via `asyncio.to_thread`.

## Commands

| Task | Command |
|---|---|
| Install | `uv sync` |
| Run app | `uv run main.py` (Administrator terminal) |
| Docs preview | `uv run properdocs serve` |
| Docs build | `uv run properdocs build` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Lint+Format | `ruff check . && ruff format .` |
| Build exe | `uv run pyinstaller --name "PyMonitor" -p .\app\ main.py --noconsole --onefile` |

No `pytest`/`mypy` deps in `pyproject.toml` yet - run if configured locally.

## Settings & Secrets

* **Never hardcode** tokens/paths. Use `PYMONITOR__` env prefix (`app/settings.py:20`). Add new settings as `BaseSettings` subclasses with `env_prefix` logic.
* `.env` is loaded via `pydantic-settings` (`env_file=".env"`). Keep `.env.example` up to date.
* Computed fields: `base_path` (frozen vs dev), `assets_path`, `root_path`, `logging_config`. Don't compute paths manually.

## Logging

* **Handler**: `RotatingFileHandler` `app.log` 10MB x5 + `StreamHandler` stdout/stderr (`app/settings.py:105`). Don't switch to console-only.
* **Get logger**: `from app.services.log import get_logger; get_logger().info(...)` (name `"pymonitor"`).
* **Levels**: `PYMONITOR__LOG_LEVEL` controls root; libraries `urllib3/httpcore/telegram/asyncio/httpx` are silenced to `INFO` (`app/settings.py:130`).
* **Assets**: `Charger-ok.mp3` etc. live in `assets/` (`assets_path`). Check `is_file()` before playing.

## Docs

* **Engine**: ProperDocs (`properdocs.yml`), not raw `mkdocs` - use `uv run properdocs serve/build`.
* **Site config**: `properdocs.yml` (Material theme `language: en`, `kroki` at `http://localhost:8080`, `mkdocstrings` with `sys.path.append(".")`, `extra_css`).
* **Location**: All sources in `docs/`. Navigation defined in `properdocs.yml:nav`.
* **Rule**: When adding a monitor (`MetricsService` + `@monitor_metric`) or action (`PyAgent.take_action`), you **must** update the relevant Markdown in `docs/` (monitors table, roadmap, API if needed). This is enforced in code review.

## Git & Style

* **Commits**: Inspect `git status`, `git diff`, `git log --oneline -10` before committing; stage only intended files; never commit secrets.
* **Format**: `ruff format` enforces style. Avoid adding emojis unless requested.
* **Types**: Pydantic models (`Event`, `Message`, `Request`) use `ConfigDict(validate_assignment=True)` etc. - respect them.
* **Telegram errors**: Catch `telegram.error.TelegramError` (base), not generic `Exception` (`app/services/interfaces.py:51,99`).

## Gotchas

* `@monitor_metric(interval=...)` param is **ignored** - all monitors sleep `check_interval`. Don't depend on per-monitor intervals.
* `StateManager.get` miss returns `Event(status=None)` - first emit always fires.
* `TelegramInterface.get_status` is a stub (logs only). Don't rely on it.
* `AlarmService` only sounds for `Charger`/`Tobii_Hardware`; missing `-nok.mp3` logs error.
* `wmi` import fails on non-Windows - guard or skip on other OS if testing locally (but app is Windows-only).
