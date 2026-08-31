import asyncio

from ..models import Event
from .interfaces import MessageInterface, get_interfaces
from .log import get_logger


class MessengerService:
    def __init__(self):
        self.logger = get_logger()
        self.interfaces: list[MessageInterface] | None = None
        self.request_queue: asyncio.Queue | None = None

    def initialize(self, queue: asyncio.Queue):
        self.interfaces = get_interfaces(request_queue=queue)
        if not self.interfaces:
            self.logger.warning("No one interface to send messages")

    async def send(self, message: Event):
        for interface in self.interfaces:
            await interface.send(message)

    async def start(self):
        self.logger.info("Starting to listen through Messenger Interfaces")
        await asyncio.gather(*[interface.listen() for interface in self.interfaces])
