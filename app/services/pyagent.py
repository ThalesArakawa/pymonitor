from .messenger import MessengerService
from .metrics import MetricsService
from .player import AudioService
from .state_manager import StateManager
import asyncio
from .log import get_logger


class PyAgent:
    def __init__(self):
        self.logger = get_logger()
        self.event_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()
        self.state_tracker = StateManager()
        self.messenger_service = MessengerService(
            queue=self.event_queue, state=self.state_tracker
        )
        self.metrics_service = MetricsService(
            queue=self.event_queue,
            audio_queue=self.audio_queue,
            state=self.state_tracker,
        )
        self.audio_service = AudioService(
            queue=self.audio_queue, state=self.state_tracker
        )
        self._initialize_services()

    def _initialize_services(self):
        self.messenger_service = asyncio.create_task(self.messenger_service.start())
        self.audio_service = asyncio.create_task(self.audio_service.start())
        self.metrics_service = asyncio.create_task(self.metrics_service.start())

    async def start(self):
        await asyncio.gather(self.messenger_service, self.metrics_service)
