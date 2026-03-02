import psutil
from .log import get_logger
from .state_manager import StateManager
from settings import get_settings
from .custom_types import MonitoringMessage
import subprocess
import asyncio
from pathlib import Path


class MetricsService:
    def __init__(
        self, queue: asyncio.Queue, audio_queue: asyncio.Queue, state: StateManager
    ):
        self.settings = get_settings()
        self.logger = get_logger()
        self.queue = queue
        self.audio_queue = audio_queue
        self.state = state
        self.valid_methods = None
        self._setup()

    def _setup(self) -> None:
        check_methods = [method for method in dir(self) if method.startswith("check_")]
        valid_methods = []
        for method_name in check_methods:
            self.logger.debug(
                f"Checking {method_name.replace('check_', '')} availability"
            )
            method = getattr(self, method_name)
            result = method
            if result is not None:
                self.logger.info(f"{method_name.replace('check_', '')} available.")
                valid_methods.append(method)
            else:
                self.logger.info(f"{method_name.replace('check_', '')} NOT available.")
                self.logger.warning(
                    f"{method_name.replace('check_', '').capitalize()} not available."
                )

        self.valid_methods = valid_methods

    async def start(self):
        tasks = [method() for method in self.valid_methods]
        await asyncio.gather(*tasks)

    async def check_locked_status(self):
        title = "System Locked Status"
        while True:
            previous_state = self.state.get(key="lock")
            current_state_ok_status = True
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "LogonUI.exe":
                    current_state_ok_status = False
                    break

            # Verifica se o estado mudou (Evita spam)
            if previous_state.ok_status != current_state_ok_status:
                self.logger.info(
                    "[Monitor Bloqueio] 🚨 Mudança detectada! Enviando para a fila..."
                )
                if current_state_ok_status:
                    content = "NOT LOCKED!"
                    ok_status = True
                else:
                    content = "LOCKED!"
                    ok_status = False

                new_event = MonitoringMessage(
                    title=title,
                    content=content,
                    ok_status=ok_status,
                )

                self.state.update_state("lock", new_event)
                await self.queue.put(new_event)

            await asyncio.sleep(self.settings.monitoring.check_interval)  # Aguarda 5 segundos até a próxima checagem

    async def check_optikey_status(self):
        title = "Optikey Status"
        while True:
            previous_state = self.state.get(key="optikey_status")
            current_state_ok_status = False
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == self.settings.tobii.optikey_exe_name:
                    current_state_ok_status = True
                    break

            # Verifica se o estado mudou (Evita spam)
            if previous_state.ok_status != current_state_ok_status:
                if current_state_ok_status:
                    self.logger.info("Optikey Aberto")
                else:
                    self.logger.info("Optikey Fechado")

                if current_state_ok_status:
                    content = "UP!"
                    ok_status = True
                else:
                    content = "NOT UP!"
                    ok_status = False
                    try:
                        self.logger.info(f"Reabrindo Optikey...")
                        optikey_path = Path(self.settings.tobii.optikey_path)
                        subprocess.Popen([optikey_path])
                    except FileNotFoundError:
                        self.logger.error(
                            f"Falha ao abrir: O executável do Optikey não foi encontrado em {optikey_path}"
                        )

                    except PermissionError:
                        self.logger.error(
                            f"Falha ao abrir: Sem permissão para executar o Optikey em {optikey_path}"
                        )

                    except Exception:
                        # Usar .exception() no lugar de .error() anexa automaticamente o stack trace completo ao log
                        self.logger.exception(
                            "Erro inesperado ao tentar abrir o Optikey."
                        )

                new_event = MonitoringMessage(
                    title=title,
                    content=content,
                    ok_status=ok_status,
                )

                self.state.update_state(key="optikey_status", content=new_event)
                self.logger.debug(
                    "[Optikey] 🚨 Mudança detectada! Enviando para a fila..."
                )
                await self.queue.put(new_event)

            await asyncio.sleep(self.settings.monitoring.check_interval)

    
    async def check_anydesk_status(self):
        title = "Anydesk Status"
        while True:
            previous_state = self.state.get(key="anydesk_status")
            current_state_ok_status = False
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == self.settings.remote_access.anydesk_exe_name:
                    current_state_ok_status = True
                    break

            # Verifica se o estado mudou (Evita spam)
            if previous_state.ok_status != current_state_ok_status:
                if current_state_ok_status:
                    self.logger.info("AnyDesk Aberto")
                else:
                    self.logger.info("AnyDesk Fechado")

                if current_state_ok_status:
                    content = "UP!"
                    ok_status = True
                else:
                    content = "NOT UP!"
                    ok_status = False
                    try:
                        self.logger.info(f"Reabrindo AnyDesk...")
                        anydesk_path = Path(self.settings.remote_access.anydesk_path)
                        subprocess.Popen([anydesk_path])
                    except FileNotFoundError:
                        self.logger.error(
                            f"Falha ao abrir: O executável do AnyDesk não foi encontrado em {anydesk_path}"
                        )

                    except PermissionError:
                        self.logger.error(
                            f"Falha ao abrir: Sem permissão para executar o AnyDesk em {anydesk_path}"
                        )

                    except Exception:
                        # Usar .exception() no lugar de .error() anexa automaticamente o stack trace completo ao log
                        self.logger.exception(
                            "Erro inesperado ao tentar abrir o AnyDesk."
                        )

                new_event = MonitoringMessage(
                    title=title,
                    content=content,
                    ok_status=ok_status,
                )

                self.state.update_state(key="anydesk_status", content=new_event)
                self.logger.debug(
                    "[AnyDesk] 🚨 Mudança detectada! Enviando para a fila..."
                )
                await self.queue.put(new_event)

            await asyncio.sleep(self.settings.monitoring.check_interval)

    async def check_tobii_status(self):
        title = "Tobii Status"
        while True:
            previous_state = self.state.get(key="tobii_status")
            current_state = {
                self.settings.tobii.eyex_engine_exe_name: False,
                self.settings.tobii.eyex_interaction_exe_name: False,
                self.settings.tobii.service_exe_name: False,
                self.settings.tobii.service_name: False,
                self.settings.tobii.generic_name: False,
                self.settings.tobii.eyetracker_name: False,
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
                    if not current_state[service_name]:
                        subprocess.Popen(['sc', 'stop', service_name]) # Using sc command via subprocess
                        await asyncio.sleep(15)
                        self.logger.info(f"Starting {service_name}...")
                        subprocess.Popen(['sc', 'start', service_name]) # Using sc command via subprocess
                        self.logger.info(f"{service_name} started.")
                except psutil.NoSuchProcess as e:
                    current_state[service_name] = False
                except Exception as e:
                    self.logger.error(f"Erro desconhecido encontrado")

            # Verifica se o estado mudou (Evita spam)

            diff = False
            full_content = ""
            ok_status = True
            for key, values in current_state.items():
                content = ""
                if (
                    current_state[key]
                    != previous_state.get(
                        key,
                        MonitoringMessage(
                            title="",
                            content="",
                            ok_status=None,
                        ),
                    ).ok_status
                ):
                    diff = True
                if current_state[key]:
                    full_content += f"{key} UP\n"
                    content += f"{key} UP\n"
                    ok_status = True
                else:
                    full_content += f"{key} DOWN\n"
                    content += f"{key} DOWN\n"
                    ok_status = False

                current_state[key] = MonitoringMessage(
                    title=key,
                    content=content,
                    ok_status=ok_status,
                )

            if diff:

                self.state.update_state(key="tobii_status", content=current_state)
                self.logger.debug(
                    "[Tobii] 🚨 Mudança detectada! Enviando para a fila..."
                )
                await self.queue.put(
                    MonitoringMessage(
                        title=title,
                        content=full_content,
                        ok_status=ok_status,
                    )
                )

            await asyncio.sleep(self.settings.monitoring.check_interval)

    async def check_charger_status(self):
        title = "Charger Status"
        while True:
            previous_state = self.state.get(key="battery")
            current_state_ok_status = False
            battery_stats = psutil.sensors_battery()

            if battery_stats is None:
                self.logger.warning("Battery information not available.")
                content = "Battery information not available."
                current_state_ok_status = None
                value = None
            else:
                if battery_stats.power_plugged:
                    content = f"Charger is connected. Battery percentage: {battery_stats.percent}%"
                    current_state_ok_status = True

                else:
                    content = f"Charger is NOT connected. Battery percentage: {battery_stats.percent}%"
                    current_state_ok_status = False
                value = battery_stats.percent

            if previous_state.ok_status != current_state_ok_status or int(
                previous_state.value
            ) != int(value):
                content = MonitoringMessage(
                    title=title,
                    content=content,
                    ok_status=current_state_ok_status,
                    value=str(value),
                )
                if content.ok_status:
                    if (
                        previous_state.ok_status is not None
                        and previous_state.ok_status is not True
                    ):
                        await self.audio_queue.put("battery_connected")
                else:
                    if previous_state.ok_status or previous_state.ok_status is None:
                        await self.audio_queue.put("battery_disconnected")
                    elif int(content.value) % 5 == 0:
                        await self.audio_queue.put("battery_disconnected")

                if previous_state.ok_status != current_state_ok_status:
                    if current_state_ok_status:
                        self.logger.info("Charger is connected.")
                    else:
                        self.logger.warning("Charger is not connected.")
                    self.logger.debug(
                        "[Monitor Bateria] 🚨 Mudança detectada! Enviando para a fila..."
                    )
                    self.state.update_state(key="battery", content=content)
                    await self.queue.put(content)

            await asyncio.sleep(self.settings.monitoring.check_interval)

    async def check_network_status(self):
        title = "Network Status"
        while True:
            previous_state = self.state.get("network")
            ethernet_state = psutil.net_if_stats().get("Ethernet").isup
            wifi_state = psutil.net_if_stats().get("Wi-Fi").isup
            current_state_ok_status = False
            if ethernet_state or wifi_state:
                content = "Network is connected."
                current_state_ok_status = True
            else:
                content = "No network connection detected."
                current_state_ok_status = False

            current_state = MonitoringMessage(
                title=title, content=content, ok_status=current_state_ok_status
            )

            if previous_state.ok_status != current_state_ok_status:
                if current_state_ok_status:
                    self.logger.debug("Network is connected.")
                else:
                    self.logger.warning("No network connection detected.")
                self.state.update_state(key="network", content=current_state)

                self.logger.info(
                    "[Monitor Rede] 🚨 Mudança detectada! Enviando para a fila..."
                )
                await self.queue.put(current_state)

            await asyncio.sleep(self.settings.monitoring.check_interval)
