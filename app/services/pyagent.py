import asyncio
import subprocess
from pathlib import Path

import aiofiles
import cv2

from ..models import Event, Message, Request
from ..settings import get_settings
from .alarm import AlarmService
from .database import DataBaseConnector
from .log import get_logger
from .messenger import MessengerService


class PyAgent:
    def __init__(self, messenger: MessengerService):
        self.logger = get_logger()
        self.settings = get_settings()
        self.event_queue: asyncio.Queue | None = []
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.state_tracker: DataBaseConnector | None = None
        self.messenger_service: MessengerService = messenger
        self.alarm_service: AlarmService = AlarmService()
        self.messenger_service.initialize(queue=self.request_queue)

    def set_event_queue(self, queue: asyncio.Queue):
        self.event_queue = queue

    def set_state_tracker(self, database_connector: DataBaseConnector):
        self.state_tracker = database_connector

    def get_photo(self):
        # Initialize the webcam (0 represents the default camera)
        cap = cv2.VideoCapture(0)

        # Check if the webcam opened successfully
        if not cap.isOpened():
            self.logger.error("Error: Could not open webcam.")
            photo = None

        # Capture a single frame
        ret, frame = cap.read()
        cap.release()
        # Check if the frame was captured successfully
        if ret:
            # Display the captured frame (optional)
            is_success, buffer = cv2.imencode(".jpeg", frame)
            if not is_success:
                self.logger.error("Error: Could not encode image.")
                return None

            # Save the captured frame as an image file
            photo = buffer.tobytes()

        else:
            self.logger.error("Error: Failed to capture frame.")

        return photo

    async def get_log(self) -> bytes:
        try:
            async with aiofiles.open(
                self.settings.base_path.parent / "app.log", mode="rb"
            ) as f:
                log = await f.read()
        except FileNotFoundError as e:
            self.logger.error(f"Log file NOT Found: {e}")
            log = b""

        return log

    async def respond(self, request: Request):
        if request.message == "photo":
            return Message(
                content="Aqui está a foto da WebCam:",
                byte_content=self.get_photo(),
                recipient=request.update,
                type="photo",
            )
        elif request.message == "log":
            log = await self.get_log()
            if log:
                content = "Aqui está o log:"
            else:
                content = "Não foi possível obter o log"
            return Message(
                content=content,
                byte_content=log,
                recipient=request.update,
                type="doc",
            )
        else:
            return Message(content="Método não implementado!")

    def restart_tobii_service(self, event: Event) -> bool:
        services = [
            self.settings.tobii.service_name,
            self.settings.tobii.generic_name,
            self.settings.tobii.eyetracker_name,
        ]

        try:
            for service_name in services:
                # Stop the service
                stop_command = ["sc", "stop", service_name]
                subprocess.run(
                    stop_command,
                    check=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                )
                self.logger.info(f"{service_name} stopped.")

                # Start the service
                start_command = ["sc", "start", service_name]
                subprocess.run(
                    start_command,
                    check=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    text=True,
                )
                self.logger.info(f"{service_name} started.")

            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error executing command: {e.stderr}\n{e.stdout}")
            self.logger.error(
                "Note: Ensure the service name is correct and the script is run as an administrator."
            )

        return False

    async def restart_optikey(self, event: Event) -> bool:
        optikey_path = Path(self.settings.tobii.optikey_path)
        if not optikey_path.is_file():
            self.logger.error(f"Arquivo do OptiKey não foi encontrado: {optikey_path}")
            return False
        try:
            # Kill Optikey process
            args = [
                "-f",
                "-im",
                self.settings.tobii.optikey_exe_name,
            ]
            await asyncio.create_subprocess_exec(
                "taskkill",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Open Optikey process
            await asyncio.create_subprocess_exec(
                optikey_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.logger.info("Optikey started.")

            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error executing command: {e.stderr}\n{e.stdout}")
            self.logger.error("Note: Ensure the Optikey Path.")

        return False

    async def restart_anydesk(self, event: Event) -> bool:
        anydesk_path = Path(self.settings.remote_access.anydesk_path)
        if not anydesk_path.is_file():
            self.logger.error(f"Arquivo do AnyDesk não foi encontrado: {anydesk_path}")
            return False
        try:
            # Kill Anydesk process
            kill_command = [
                "-f",
                "-im",
                self.settings.remote_access.anydesk_exe_name,
            ]
            await asyncio.create_subprocess_exec(
                "taskkill",
                *kill_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Open Anydesk process
            await asyncio.create_subprocess_exec(
                anydesk_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.logger.info("Anydesk started.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error executing command: {e.stderr}\n{e.stdout}")
            self.logger.error("Note: Ensure the Anydesk Path.")
        return False

    async def take_action(self, event: Event) -> bool | None:
        resource_name = event.resource_name
        if resource_name == "Tobii_Services":
            result = await asyncio.to_thread(self.restart_tobii_service, event)
        elif resource_name == "Optikey":
            result = await self.restart_optikey(event=event)
        elif resource_name == "AnyDesk":
            result = await self.restart_anydesk(event=event)
        else:
            return None
        return result

    def create_message(self, event: Event) -> Message:
        return Message(content=event.message)

    async def active_monitoring(self):
        while True:
            event: Event = await self.event_queue.get()
            if not event.status:
                await self.take_action(event=event)
            message: Message = self.create_message(event=event)

            tasks = []
            tasks.append(
                asyncio.create_task(self.messenger_service.send(message=message))
            )
            tasks.append(
                asyncio.create_task(self.alarm_service.send_alarm(event=event))
            )

            await asyncio.gather(*tasks)

            self.logger.debug("Finished Event")

            self.event_queue.task_done()

    async def passive_monitoring(self):
        while True:
            request: Request = await self.request_queue.get()
            message = await self.respond(request=request)
            await self.messenger_service.send(message=message)
            self.request_queue.task_done()

    async def start(self):
        self.logger.info("Starting Agent")
        tasks = []
        tasks.append(asyncio.create_task(self.messenger_service.start()))
        tasks.append(asyncio.create_task(self.active_monitoring()))
        tasks.append(asyncio.create_task(self.passive_monitoring()))

        await asyncio.gather(*tasks)
