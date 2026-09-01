import asyncio
import functools
import inspect
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import psutil

try:
    import wmi as wmi_module  # type: ignore[import-untyped]
except ImportError:
    wmi_module = None  # type: ignore[assignment]

from ..models import Event
from ..settings import AppSettings, get_settings
from .database import DataBaseConnector
from .log import get_logger


class MetricCollectionError(RuntimeError):
    """Base error for metric collection failures."""


class WMIUnavailableError(MetricCollectionError):
    """Raised when WMI is unavailable or query fails."""


class ProcessLookupError(MetricCollectionError):
    """Raised when process iteration fails."""


class NetworkLookupError(MetricCollectionError):
    """Raised when network interface lookup fails."""


class BatteryLookupError(MetricCollectionError):
    """Raised when battery info lookup fails."""


class ServiceLookupError(MetricCollectionError):
    """Raised when Windows service lookup fails."""


class LoggerProtocol(Protocol):
    def info(self, msg: object, *args: object) -> None: ...

    def debug(self, msg: object, *args: object) -> None: ...

    def warning(self, msg: object, *args: object) -> None: ...

    def error(self, msg: object, *args: object) -> None: ...

    def exception(self, msg: object, *args: object) -> None: ...


class StateTrackerProtocol(Protocol):
    def get(self, key: str) -> Event: ...

    def update_state(self, key: str, content: Event) -> None: ...


def _collect_process_names() -> set[str]:
    """Return set of running process names (blocking, call via to_thread)."""
    try:
        return {
            proc.info["name"]
            for proc in psutil.process_iter(["name"])
            if proc.info["name"]
        }
    except (psutil.AccessDenied, psutil.ZombieProcess, OSError) as exc:
        raise ProcessLookupError(str(exc)) from exc


def _get_network_states() -> tuple[Any | None, Any | None]:
    """Return (ethernet_state, wifi_state) (blocking)."""
    try:
        stats = psutil.net_if_stats()
        return stats.get("Ethernet"), stats.get("Wi-Fi")
    except OSError as exc:
        raise NetworkLookupError(str(exc)) from exc


def _get_battery_stats() -> Any | None:
    """Return battery stats or None (blocking)."""
    try:
        return psutil.sensors_battery()
    except OSError as exc:
        raise BatteryLookupError(str(exc)) from exc


def _query_wmi_devices() -> list[Any]:
    """Return WMI PnP devices (blocking)."""
    if wmi_module is None:
        raise WMIUnavailableError("wmi module unavailable on this platform")
    try:
        connection = wmi_module.WMI()
        devices = connection.Win32_PnPEntity()
        return list(devices)
    except OSError as exc:
        raise WMIUnavailableError(str(exc)) from exc


def _is_service_running(service_name: str) -> bool:
    """Return True if Windows service is running (blocking)."""
    try:
        service = psutil.win_service_get(service_name)
        return bool(service.as_dict()["status"] == "running")
    except psutil.NoSuchProcess:
        return False
    except (OSError, RuntimeError) as exc:
        raise ServiceLookupError(str(exc)) from exc


def _format_tobii_summary(states: dict[str, bool]) -> tuple[str, bool]:
    """Build human-readable Tobii status message."""
    lines: list[str] = []
    all_up = True
    for key, is_up in states.items():
        lines.append(f"{key} {'UP ✅' if is_up else 'DOWN 🚨'}")
        if not is_up:
            all_up = False
    return "\n".join(lines) + "\n", all_up


def _resolve_interval(configured: float | None, fallback: float) -> float:
    """Resolve effective sleep interval."""
    return float(configured if configured is not None else fallback)


async def _collect_and_emit(
    tracker: Any,
    queue: Any,
    logger: Any,
    resource_name: str,
    func: Callable[..., Awaitable[Event]],
    self_obj: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    """Collect metric, enrich Event and emit if status changed."""
    try:
        current_state: Event = await func(self_obj, *args, **kwargs)
        current_state.timestamp = datetime.now(tz=UTC)
        current_state.event_id = str(uuid.uuid4())
        current_state.resource_name = resource_name
        previous_state: Event = tracker.get(resource_name)
        if previous_state.status != current_state.status:
            tracker.update_state(key=resource_name, content=current_state)
            logger.info("Enviando evento...")
            await queue.put(current_state)
    except (
        MetricCollectionError,
        ProcessLookupError,
        NetworkLookupError,
        BatteryLookupError,
        WMIUnavailableError,
        ServiceLookupError,
    ):
        logger.exception(f"Falha ao coletar {resource_name}")
    except (OSError, RuntimeError):  # fmt: skip
        logger.exception(f"Erro inesperado de OS em {resource_name}")


def monitor_metric(
    resource_name: str, interval: float | None = None
) -> Callable[[Callable[..., Awaitable[Event]]], Callable[..., Awaitable[None]]]:
    """Decorator injecting polling loop, change detection and queue dispatch."""

    def decorator(
        func: Callable[..., Awaitable[Event]],
    ) -> Callable[..., Awaitable[None]]:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
            display = _resolve_interval(
                interval, self.settings.monitoring.check_interval
            )
            self.logger.info(
                f"[Motor] Coletando dados: {resource_name} (a cada {display}s)"
            )
            while True:
                await _collect_and_emit(
                    self.state_tracker,
                    self.event_queue,
                    self.logger,
                    resource_name,
                    func,
                    self,
                    args,
                    kwargs,
                )
                await asyncio.sleep(
                    _resolve_interval(interval, self.settings.monitoring.check_interval)
                )

        wrapper._is_monitor = True  # type: ignore[attr-defined]
        return wrapper

    return decorator


class MetricsService:
    """Collects Windows health metrics and emits Events on status changes."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        logger: logging.Logger | LoggerProtocol | None = None,
    ) -> None:
        self.settings: AppSettings = settings or get_settings()
        self.logger: logging.Logger | LoggerProtocol = logger or get_logger()
        self.event_queue: asyncio.Queue[Event] | None = None
        self.state_tracker: DataBaseConnector | StateTrackerProtocol | None = None
        self.valid_methods: list[Callable[..., Awaitable[None]]] = []
        self._setup()

    def set_event_queue(self, queue: asyncio.Queue[Event]) -> None:
        self.event_queue = queue

    def set_state_tracker(
        self, database_connector: DataBaseConnector | StateTrackerProtocol
    ) -> None:
        self.state_tracker = database_connector

    def _setup(self) -> None:
        """Discover methods decorated with @monitor_metric."""
        for _name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, "_is_monitor", False):
                self.valid_methods.append(cast(Callable[..., Awaitable[None]], method))

    async def start(self) -> None:
        tasks = [method() for method in self.valid_methods]
        await asyncio.gather(*tasks)

    @monitor_metric(resource_name="Locked OS", interval=60)
    async def locked_status(self) -> Event:
        process_names = await asyncio.to_thread(_collect_process_names)
        is_locked = "LogonUI.exe" in process_names
        message = "TELA BLOQUEADA!! 🚨" if is_locked else "Tela desbloqueada ✅"
        self.logger.debug(message)
        return Event(message=message, status=not is_locked)

    @monitor_metric(resource_name="Optikey", interval=60)
    async def optikey_status(self) -> Event:
        process_names = await asyncio.to_thread(_collect_process_names)
        is_open = self.settings.tobii.optikey_exe_name in process_names
        message = "Optikey Aberto ✅" if is_open else "Optikey Fechado 🚨"
        self.logger.debug(message)
        return Event(message=message, status=is_open)

    @monitor_metric(resource_name="AnyDesk", interval=60)
    async def anydesk_status(self) -> Event:
        process_names = await asyncio.to_thread(_collect_process_names)
        is_open = self.settings.remote_access.anydesk_exe_name in process_names
        message = "AnyDesk Aberto ✅" if is_open else "AnyDesk FECHADO!!! 🚨"
        self.logger.debug(message)
        return Event(message=message, status=is_open)

    @monitor_metric(resource_name="Network", interval=60)
    async def network_status(self) -> Event:
        ethernet_state, wifi_state = await asyncio.to_thread(_get_network_states)
        is_up = bool(
            (ethernet_state and ethernet_state.isup) or (wifi_state and wifi_state.isup)
        )
        message = "Conectado a Rede ✅" if is_up else "NÃO CONECTADO A REDE!!! 🚨"
        self.logger.debug(message)
        return Event(message=message, status=is_up)

    @monitor_metric(resource_name="Charger", interval=60)
    async def charger_status(self) -> Event:
        battery_stats = await asyncio.to_thread(_get_battery_stats)
        if battery_stats is None:
            self.logger.warning("Battery information not available.")
            return Event(
                message="Battery information not available.",
                status=None,
                value=None,
            )
        is_plugged = bool(battery_stats.power_plugged)
        percent = battery_stats.percent
        message = (
            f"Bateria Conectada {percent}% ✅"
            if is_plugged
            else f"Bateria DESCONECTADA {percent}% !!! 🚨"
        )
        self.logger.debug(message)
        return Event(message=message, status=is_plugged, value=percent)

    @monitor_metric(resource_name="Tobbi_Hardware", interval=60)
    async def tobii_hardware_status(self) -> Event:
        devices = await asyncio.to_thread(_query_wmi_devices)
        is_connected = any(
            device.Name and "tobii" in device.Name.lower() for device in devices
        )
        message = "Tobii conectado ✅" if is_connected else "Tobii desconectado!!! 🚨"
        self.logger.debug(message)
        return Event(message=message, status=is_connected)

    @monitor_metric(resource_name="Tobii_Services", interval=60)
    async def check_tobii_status(self) -> Event:
        tobii_executables = [
            self.settings.tobii.eyex_engine_exe_name,
            self.settings.tobii.eyex_interaction_exe_name,
            self.settings.tobii.service_exe_name,
        ]
        tobii_services = [
            self.settings.tobii.service_name,
            self.settings.tobii.generic_name,
            self.settings.tobii.eyetracker_name,
        ]
        process_names = await asyncio.to_thread(_collect_process_names)
        states: dict[str, bool] = {
            self.settings.tobii.service_name: False,
            self.settings.tobii.generic_name: False,
            self.settings.tobii.eyetracker_name: False,
            self.settings.tobii.eyex_engine_exe_name: False,
            self.settings.tobii.eyex_interaction_exe_name: False,
            self.settings.tobii.service_exe_name: False,
        }
        for exe_name in tobii_executables:
            states[exe_name] = exe_name in process_names
        for service_name in tobii_services:
            states[service_name] = await asyncio.to_thread(
                _is_service_running, service_name
            )
        message, is_ok = _format_tobii_summary(states)
        self.logger.debug(message)
        return Event(message=message, status=is_ok)
