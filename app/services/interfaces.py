from telegram.ext import Application, CommandHandler, CallbackContext
from telegram import Update
from ..settings import get_settings
from functools import cache
import asyncio
from .log import get_logger
from .database import StateManager
import uuid
from datetime import datetime
import io
from abc import ABC
from ..models import Message, Request

from typing import List


class MessageInterface(ABC):

    @classmethod
    async def send(self, message: Message) -> bool:
        pass


def format_message(message: Message):
    if message.byte_content:
        return message.byte_content
    return message.content


class TelegramInterface(MessageInterface):
    def __init__(self, request_queue: asyncio.Queue):
        self.request_queue = request_queue
        self._token = get_settings().telegram.bot_token
        self._chat_id = get_settings().telegram.chat_id
        self.settings = get_settings()
        self.logger = get_logger()
        self.application = Application.builder().token(self._token).build()
        self.connected = False
        self.photo_mode = get_settings().monitoring.photo_mode

    async def listen(self) -> None:
        self.logger.info("Starting to listen to Telegram Interface")
        self.application.add_handler(CommandHandler("status", self.get_status))
        self.application.add_handler(CommandHandler("log", self.get_log))
        if self.photo_mode:
            self.application.add_handler(CommandHandler("photo", self.get_photo))
        while not self.connected:
            try:
                await self.application.initialize()
                await self.application.start()
                self.connected = True
                await self.application.updater.start_polling()
            except Exception as e:
                self.logger.error(f"Failed to connect to Telegram {e}")
                self.connected = False
                await asyncio.sleep(360)

    async def get_status(self, update: Update, context: CallbackContext):
        self.logger.debug("Getting Status")
        pass

    async def get_log(self, update: Update, context: CallbackContext):
        self.logger.info("Log requisitada via Telegram")
        await self.request_queue.put(
            Request(
                request_id=str(uuid.uuid4()),
                message="log",
                timestamp=datetime.now(),
                update=update,
            )
        )

    async def get_photo(self, update: Update, context: CallbackContext):
        self.logger.info("Foto requisitada via Telegram")
        await self.request_queue.put(
            Request(
                request_id=str(uuid.uuid4()),
                message="photo",
                timestamp=datetime.now(),
                update=update,
            )
        )

    async def send(self, message: Message):
        response = format_message(message)
        if self.application:
            if message.type == "photo":
                await message.recipient.message.reply_photo(response)
            elif message.type == "doc":
                log_file = io.BytesIO(response)
                await message.recipient.message.reply_document(
                    document=log_file, filename="application_log.txt"
                )
            else:
                self.logger.debug(f"Periodic Update: Sending HTML message to Telegram.")
                try:
                    await self.application.bot.send_message(
                        chat_id=self._chat_id,
                        text=response,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    self.logger.error(f"Erro desconhecido: {e}")
        else:
            self.logger.error("Telegram bot is not set up. Cannot send message.")


def get_interfaces(request_queue: asyncio.Queue) -> List[MessageInterface]:
    return [TelegramInterface(request_queue=request_queue)]
