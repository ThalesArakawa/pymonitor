from .log import get_logger
from .custom_types import MonitoringMessage
from settings import get_settings, AppSettings
import asyncio
from .interfaces import get_interfaces
from functools import cache

class Messenger:
    def __init__(self):
        self.logger = get_logger()
        self.interfaces = get_interfaces()

    async def send_message(self, message: list):
        for interface in self.interfaces.values():
            try:
                await interface.send_message(message)
            except Exception as e:
                self.logger.error(f"Failed to send message via {interface.__class__.__name__}: {e}")
    
    async def receive_message(self):
        if update.message:
            self.logger.info(f"Received message: {update.message.text}")
            # Process the message as needed
            context.bot.send_message(chat_id=update.effective_chat.id, text="Message received.")
        else:
            self.logger.warning("Received an update without a message.")

@cache
def get_messenger() -> Messenger:
    settings = get_settings()
    return Messenger()