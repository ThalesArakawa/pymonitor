import psutil
from .log import get_logger
from .database import DataBaseConnector
from ..settings import get_settings
import uuid
from datetime import datetime
import inspect
import asyncio
from ..models import Event

import asyncio
import functools
import wmi


def monitor_metric(resource_name, interval: float = 5.0):
    """
    Invólucro que injeta o loop de repetição, a avaliação de conformidade
    e o envio automático para a fila de eventos.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            self.logger.info(
                f"[Motor] Coletando dados: {resource_name} (a cada {interval}s)"
            )

            while True:
                try:
                    # 1. COLLECT METRIC
                    current_state: Event = await func(self, *args, **kwargs)
                    current_state.timestamp = datetime.now()
                    current_state.event_id = str(uuid.uuid4())
                    current_state.resource_name = resource_name

                    # 2. AVAIL METRIC
                    previous_state: Event = self.state_tracker.get(resource_name)

                    # 3. TO THE QUEUE IF HAS STATE ALTERATION
                    if previous_state.status != current_state.status:
                        self.state_tracker.update_state(
                            key=resource_name, content=current_state
                        )

                        self.logger.info("Enviando evento...")
                        await self.event_queue.put(current_state)

                except Exception as e:
                    self.logger.error(f"[Erro no Monitor {resource_name}]: {e}")

                # 4. interval: O decorator cuida do tempo de espera
                await asyncio.sleep(self.settings.monitoring.check_interval)

        # Etiquetamos o wrapper para o setup encontrar
        wrapper._is_monitor = True
        return wrapper

    return decorator


class MetricsService:
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger()
        self.event_queue = None
        self.state_tracker: DataBaseConnector | None = None
        self.valid_methods = []
        self._setup()

    def set_event_queue(self, queue: asyncio.Queue):
        self.event_queue = queue

    def set_state_tracker(self, database_connector: DataBaseConnector):
        self.state_tracker = database_connector

    def _setup(self) -> None:
        """Apenas encontra os métodos decorados e salva a referência."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, "_is_monitor", False):
                self.valid_methods.append(method)

    async def start(self):
        # Como o próprio decorator já tem o 'while True' dentro dele,
        # chamar method() apenas inicializa a corrotina do loop infinito.
        tasks = [method() for method in self.valid_methods]
        # tasks.append(self.consumidor_telegram())

        await asyncio.gather(*tasks)

    @monitor_metric(resource_name="Locked OS", interval=60)
    async def locked_status(self) -> Event:
        current_state_ok_status = True
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == "LogonUI.exe":
                current_state_ok_status = False
                break

        if current_state_ok_status:
            message = "Tela desbloqueada ✅"
        else:
            message = "TELA BLOQUEADA!! 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )

    @monitor_metric(resource_name="Optikey", interval=60)
    async def optikey_status(self) -> Event:
        current_state_ok_status = False
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == self.settings.tobii.optikey_exe_name:
                current_state_ok_status = True
                break

        if current_state_ok_status:
            message = "Optikey Aberto ✅"
        else:
            message = "Optikey Fechado 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )

    @monitor_metric(resource_name="AnyDesk", interval=60)
    async def anydesk_status(self) -> Event:
        current_state_ok_status = False
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == self.settings.remote_access.anydesk_exe_name:
                current_state_ok_status = True
                break

        if current_state_ok_status:
            message = "AnyDesk Aberto ✅"
        else:
            message = "AnyDesk FECHADO!!! 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )

    @monitor_metric(resource_name="Network", interval=60)
    async def network_status(self):
        ethernet_state = psutil.net_if_stats().get("Ethernet")
        wifi_state = psutil.net_if_stats().get("Wi-Fi")
        current_state_ok_status = False
        if (ethernet_state and ethernet_state.isup) or (wifi_state and wifi_state.isup):
            current_state_ok_status = True
        else:
            current_state_ok_status = False

        if current_state_ok_status:
            message = "Conectado a Rede ✅"
        else:
            message = "NÃO CONECTADO A REDE!!! 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )

    @monitor_metric(resource_name="Charger", interval=60)
    async def charger_status(self):
        current_state_ok_status = False
        battery_stats = psutil.sensors_battery()

        if battery_stats is None:
            self.logger.warning("Battery information not available.")
            content = "Battery information not available."
            current_state_ok_status = None
            value = None
        else:
            current_state_ok_status = battery_stats.power_plugged
            value = battery_stats.percent

        if current_state_ok_status:
            message = f"Bateria Conectada {value}% ✅"
        else:
            message = f"Bateria DESCONECTADA {value}% !!! 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
            value=value,
        )

    @monitor_metric(resource_name="Tobbi_Hardware", interval=60)
    async def tobii_hardware_status(self):
        wmi_connection = wmi.WMI()
        devices = wmi_connection.Win32_PnPEntity()
        current_state_ok_status = False
        for device in devices:
            if device.Name and "tobii" in device.Name.lower():
                current_state_ok_status = True

        if current_state_ok_status:
            message = f"Tobii conectado ✅"
        else:
            message = f"Tobii desconectado!!! 🚨"

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )

    @monitor_metric(resource_name="Tobii_Services", interval=60)
    async def check_tobii_status(self):
        current_state = {
            self.settings.tobii.service_name: False,
            self.settings.tobii.generic_name: False,
            self.settings.tobii.eyetracker_name: False,
            self.settings.tobii.eyex_engine_exe_name: False,
            self.settings.tobii.eyex_interaction_exe_name: False,
            self.settings.tobii.service_exe_name: False,
        }
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
        for proc in psutil.process_iter(["name"]):
            for exe_name in tobii_executables:
                if proc.info["name"] == exe_name:
                    current_state[exe_name] = True

        for service_name in tobii_services:
            try:
                service = psutil.win_service_get(service_name)
                current_state[service_name] = (
                    True if service.as_dict()["status"] == "running" else False
                )
            except psutil.NoSuchProcess:
                current_state[service_name] = False
            except Exception as e:
                self.logger.error(f"Erro desconhecido encontrado")

        message = ""
        current_state_ok_status = True
        for key, values in current_state.items():
            if current_state[key]:
                message += f"{key} UP ✅\n"
            else:
                message += f"{key} DOWN 🚨\n"
                current_state_ok_status = False

        self.logger.debug(message)
        return Event(
            message=message,
            status=current_state_ok_status,
        )
