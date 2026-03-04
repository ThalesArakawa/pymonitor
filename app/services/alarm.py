from .log import get_logger
import asyncio
from playsound3 import playsound
from ..settings import get_settings
from ..models import Event
from pathlib import Path


class AlarmService:
    def __init__(self):
        self.logger = get_logger()
        self.settings = get_settings()
        self.alarm_state = {}
        self.tasks = {}

    async def send_alarm(self, event: Event):
        if event.resource_name in ["Charger", "Tobii_Hardware"]:
            await self.play_alarm(event=event)

    async def play_alarm(self, event: Event):
        resource_name = event.resource_name
        self.logger.debug(f"Playing Audio for {resource_name}")

        if event.status:
            task = self.tasks.get(resource_name)
            if task and not task.done():
                self.alarm_state[
                    resource_name
                ].set()
                await task
                self.tasks[resource_name] = None
                await self.on_success(
                    audio=self.settings.assets_path / f"{resource_name}-ok.mp3",
                    resource_name=resource_name,
                )
        else:
            task = self.tasks.get(resource_name)
            if task is None or task.done():
                self.alarm_state[resource_name] = asyncio.Event()
                self.tasks[resource_name] = asyncio.create_task(
                    self.on_failure(
                        audio=self.settings.assets_path / f"{resource_name}-nok.mp3",
                        resource_name=resource_name,
                    )
                )

    async def on_failure(self, audio: Path, resource_name: str):
        self.logger.error(f"Playing Alarm for {resource_name}")
        file_path = audio
        if not file_path.is_file():
            self.logger.error(f"The file {file_path} does not exist or is not a file.")
            return
        while not self.alarm_state[resource_name].is_set():
            await asyncio.to_thread(playsound, str(audio), False)

            try:
                await asyncio.wait_for(
                    self.alarm_state[resource_name].wait(), timeout=self.settings.alarm.interval
                )
                break

            except asyncio.TimeoutError:
                self.logger.error(f"Playing alarm for {resource_name}, again")

    async def on_success(self, audio: Path, resource_name: str):
        self.logger.info(f"Playing Correction Audio for {resource_name}")
        file_path = audio
        if not file_path.is_file():
            self.logger.error(f"The file {file_path} does not exist or is not a file.")
            return
        await asyncio.to_thread(playsound, str(audio), False)
