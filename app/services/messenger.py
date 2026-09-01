import asyncio
from typing import Any

from ..models import Event
from .interfaces import MessageInterface, get_interfaces
from .log import get_logger


class MessengerService:
    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger()
        self.interfaces: list[MessageInterface] = []
        self.request_queue: asyncio.Queue[Any] | None = None

    def initialize(self, queue: asyncio.Queue[Any]) -> None:
        self.interfaces = get_interfaces(request_queue=queue) or []
        if not self.interfaces:
            self.logger.warning("No interface to send messages")

    async def send(self, message: Event | Any) -> None:
        for interface in list(self.interfaces):
            try:
                await interface.send(message)
            except OSError, RuntimeError:
                self.logger.exception("Messenger send failed")
            except Exception:
                self.logger.exception("Unexpected messenger send")

    async def start(self) -> None:
        self.logger.info("Starting to listen through Messenger Interfaces")
        if not self.interfaces:
            self.logger.warning("No interfaces to listen")
            return
        try:
            await asyncio.gather(*[interface.listen() for interface in self.interfaces])
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger.exception("Messenger start failed")
