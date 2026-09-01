import asyncio
import logging
from pathlib import Path
from typing import Final

from playsound3 import playsound

from ..models import Event
from ..settings import AppSettings, get_settings
from .log import get_logger

ALARMED_RESOURCES: Final[frozenset[str]] = frozenset({"Charger", "Tobii_Hardware"})


class AlarmService:
    def __init__(
        self,
        settings: AppSettings | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger: logging.Logger = logger or get_logger()
        self.settings: AppSettings = settings or get_settings()
        self.alarm_state: dict[str, asyncio.Event] = {}
        self.tasks: dict[str, asyncio.Task[None] | None] = {}

    async def send_alarm(self, event: Event) -> None:
        if event.resource_name in ALARMED_RESOURCES:
            await self.play_alarm(event=event)

    async def play_alarm(self, event: Event) -> None:
        resource_name = str(event.resource_name)
        self.logger.debug(f"Playing Audio for {resource_name}")
        if event.status:
            await self._stop_alarm(resource_name)
        else:
            await self._start_alarm(resource_name)

    async def _stop_alarm(self, resource_name: str) -> None:
        task = self.tasks.get(resource_name)
        if task and not task.done():
            state = self.alarm_state.get(resource_name)
            if state:
                state.set()
            await task
        self.tasks.pop(resource_name, None)
        self.alarm_state.pop(resource_name, None)
        await self.on_success(
            audio=self.settings.assets_path / f"{resource_name}-ok.mp3",
            resource_name=resource_name,
        )

    async def _start_alarm(self, resource_name: str) -> None:
        task = self.tasks.get(resource_name)
        if task is None or task.done():
            self.alarm_state[resource_name] = asyncio.Event()
            self.tasks[resource_name] = asyncio.create_task(
                self.on_failure(
                    audio=self.settings.assets_path / f"{resource_name}-nok.mp3",
                    resource_name=resource_name,
                )
            )

    async def on_failure(self, audio: Path, resource_name: str) -> None:
        self.logger.error(f"Playing Alarm for {resource_name}")
        if not audio.is_file():
            self.logger.error(f"The file {audio} does not exist or is not a file.")
            return
        state = self.alarm_state.get(resource_name)
        if state is None:
            return
        while not state.is_set():
            await asyncio.to_thread(playsound, str(audio), False)
            try:
                await asyncio.wait_for(
                    state.wait(),
                    timeout=self.settings.alarm.interval,
                )
                break
            except TimeoutError:
                self.logger.error(f"Playing alarm for {resource_name}, again")

    async def on_success(self, audio: Path, resource_name: str) -> None:
        self.logger.info(f"Playing Correction Audio for {resource_name}")
        if not audio.is_file():
            self.logger.error(f"The file {audio} does not exist or is not a file.")
            return
        await asyncio.to_thread(playsound, str(audio), False)
