import asyncio
import logging
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import aiofiles
import cv2

from ..models import Event, Message, Request
from ..settings import AppSettings, get_settings
from .alarm import AlarmService
from .database import DataBaseConnector
from .log import get_logger
from .messenger import MessengerService


class WebcamOpenError(RuntimeError):
    """Raised when webcam device cannot be opened."""


class FrameCaptureError(RuntimeError):
    """Raised when frame capture fails."""


class ImageEncodeError(RuntimeError):
    """Raised when JPEG encoding fails."""


class VideoCaptureProtocol(Protocol):
    def isOpened(self) -> bool: ...

    def read(self) -> tuple[bool, Any]: ...

    def release(self) -> None: ...


CaptureFactory = Callable[[int], VideoCaptureProtocol]


def _open_capture(factory: CaptureFactory, device_index: int) -> VideoCaptureProtocol:
    """Create capture device or raise WebcamOpenError."""
    capture = factory(device_index)
    if not capture.isOpened():
        try:
            capture.release()
        except OSError:
            pass
        raise WebcamOpenError(f"Could not open webcam index {device_index}.")
    return capture


def _read_frame(capture: VideoCaptureProtocol) -> Any:
    """Read single frame or raise FrameCaptureError."""
    succeeded, frame = capture.read()
    if not succeeded or frame is None:
        raise FrameCaptureError("Failed to capture frame.")
    return frame


def _encode_jpeg(frame: Any) -> bytes:
    """Encode frame to JPEG bytes or raise ImageEncodeError."""
    success, buffer = cv2.imencode(".jpeg", frame)
    if not success or buffer is None:
        raise ImageEncodeError("Could not encode image.")
    return bytes(buffer.tobytes())


class PyAgent:
    def __init__(
        self,
        messenger: MessengerService,
        settings: AppSettings | None = None,
        logger: logging.Logger | None = None,
        capture_factory: CaptureFactory | None = None,
    ) -> None:
        self.logger: logging.Logger = logger or get_logger()
        self.settings: AppSettings = settings or get_settings()
        self.event_queue: asyncio.Queue[Any] | None = None
        self.request_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.state_tracker: DataBaseConnector | None = None
        self.messenger_service: MessengerService = messenger
        self.alarm_service: AlarmService = AlarmService()
        self._capture_factory: CaptureFactory = capture_factory or (
            lambda idx: cv2.VideoCapture(idx)
        )
        self.messenger_service.initialize(queue=self.request_queue)

    def set_event_queue(self, queue: asyncio.Queue):
        self.event_queue = queue

    def set_state_tracker(self, database_connector: DataBaseConnector):
        self.state_tracker = database_connector

    async def get_photo(self) -> bytes | None:
        """Capture photo without blocking the event loop."""
        capture: VideoCaptureProtocol | None = None
        try:
            capture = await asyncio.to_thread(_open_capture, self._capture_factory, 0)
            frame = await asyncio.to_thread(_read_frame, capture)
            photo = await asyncio.to_thread(_encode_jpeg, frame)
            return photo
        except WebcamOpenError as exc:
            self.logger.error(f"Webcam unavailable: {exc}")
            return None
        except FrameCaptureError as exc:
            self.logger.error(f"Frame capture failed: {exc}")
            return None
        except ImageEncodeError as exc:
            self.logger.error(f"Image encode failed: {exc}")
            return None
        finally:
            if capture is not None:
                try:
                    await asyncio.to_thread(capture.release)
                except OSError as exc:
                    self.logger.error(f"Failed to release capture: {exc}")

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

    async def respond(self, request: Request) -> Message:
        if request.message == "photo":
            photo = await self.get_photo()
            return Message(
                content="Aqui está a foto da WebCam:",
                byte_content=photo,
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

    async def _run_subprocess(self, command: list[str], timeout: float = 15.0) -> bool:
        """Run subprocess, drain pipes, enforce timeout."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            self.logger.error(f"Executable not found: {command[0]}: {exc}")
            return False
        except OSError as exc:
            self.logger.error(f"Failed to start {command[0]}: {exc}")
            return False
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except TimeoutError as exc:
            self.logger.error(f"Command timed out: {command}: {exc}")
            try:
                process.kill()
                await process.wait()
            except OSError:
                pass
            return False
        except OSError as exc:
            self.logger.error(f"OS error during {command}: {exc}")
            return False
        if process.returncode != 0:
            self.logger.error(
                f"Command failed {command} code={process.returncode} "
                f"stdout={stdout.decode(errors='ignore')} "
                f"stderr={stderr.decode(errors='ignore')}"
            )
            return False
        return True

    async def restart_optikey(self, event: Event) -> bool:
        optikey_path = Path(self.settings.tobii.optikey_path)
        if not optikey_path.is_file():
            self.logger.error(f"Arquivo do OptiKey não foi encontrado: {optikey_path}")
            return False
        kill_ok = await self._run_subprocess(
            ["taskkill", "-f", "-im", self.settings.tobii.optikey_exe_name]
        )
        if not kill_ok:
            self.logger.warning("taskkill for OptiKey returned non-zero, continuing")
        start_ok = await self._run_subprocess([str(optikey_path)])
        if start_ok:
            self.logger.info("Optikey started.")
        return start_ok

    async def restart_anydesk(self, event: Event) -> bool:
        anydesk_path = Path(self.settings.remote_access.anydesk_path)
        if not anydesk_path.is_file():
            self.logger.error(f"Arquivo do AnyDesk não foi encontrado: {anydesk_path}")
            return False
        kill_ok = await self._run_subprocess(
            ["taskkill", "-f", "-im", self.settings.remote_access.anydesk_exe_name]
        )
        if not kill_ok:
            self.logger.warning("taskkill for AnyDesk returned non-zero, continuing")
        start_ok = await self._run_subprocess([str(anydesk_path)])
        if start_ok:
            self.logger.info("Anydesk started.")
        return start_ok

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
