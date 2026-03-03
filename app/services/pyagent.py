from .messenger import MessengerService
from .database import DataBaseConnector
from ..settings import get_settings
from ..models import Event, Message, Request
import asyncio
from .log import get_logger
import cv2
import aiofiles


class PyAgent:
    def __init__(
        self,
        messenger: MessengerService = MessengerService(),
    ):
        self.logger = get_logger()
        self.settings = get_settings()
        self.event_queue: asyncio.Queue | None = []
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.state_tracker: DataBaseConnector | None = None
        self.messenger_service: MessengerService = messenger
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

        # if not photo:
        #     await update.message.reply_text("No photo available.")
        #     return
        # await update.message.reply_photo(photo)

    async def get_log(self) -> bytes:
        try:
            async with aiofiles.open(
                self.settings.base_path.parent / "app.log", mode="rb"
            ) as f:
                log = await f.read()
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            log = b""

        return log

        # if not log:
        #     await update.message.reply_text("No log available.")
        #     return
        # await update.message.reply_document(log)

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

    async def take_action(self, event: Event):
        raise NotImplementedError("Necessita implementação de lógica de tomada de ação")

    def create_message(self, event: Event) -> Message:
        return Message(content=event.message)

    async def active_monitoring(self):
        while True:
            event: Event = await self.event_queue.get()
            # await self.take_action(event=event)
            message: Message = self.create_message(event=event)
            await self.messenger_service.send(message=message)

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
