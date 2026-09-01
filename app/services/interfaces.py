import asyncio
import io
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CallbackContext, CommandHandler

from ..models import Message, Request
from ..settings import get_settings
from .log import get_logger


class MessageInterface(ABC):
    @abstractmethod
    async def send(self, message: Message) -> None:
        pass


def format_message(message: Message) -> Any:
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
            except TelegramError as e:
                self.logger.error(f"Failed to connect to Telegram {e}")
                self.connected = False
                await asyncio.sleep(360)

    async def get_status(self, update: Update, context: CallbackContext):
        self.logger.debug("Getting Status")

    async def get_log(self, update: Update, context: CallbackContext) -> None:
        self.logger.info("Log requisitada via Telegram")
        await self.request_queue.put(
            Request(
                request_id=str(uuid.uuid4()),
                message="log",
                timestamp=datetime.now(tz=UTC),
                update=update,
            )
        )

    async def get_photo(self, update: Update, context: CallbackContext) -> None:
        self.logger.info("Foto requisitada via Telegram")
        await self.request_queue.put(
            Request(
                request_id=str(uuid.uuid4()),
                message="photo",
                timestamp=datetime.now(tz=UTC),
                update=update,
            )
        )

    async def _send_photo(self, message: Message, response: bytes) -> None:
        try:
            photo_file = io.BytesIO(response)
            await message.recipient.message.reply_photo(photo=photo_file)
        except TelegramError:
            self.logger.exception("Failed to send photo via Telegram")
        except OSError, RuntimeError:
            self.logger.exception("OS error sending photo")
        except Exception:
            self.logger.exception("Unexpected error sending photo")

    async def _send_document(self, message: Message, response: bytes) -> None:
        try:
            log_file = io.BytesIO(response)
            await message.recipient.message.reply_document(
                document=log_file, filename="application_log.txt"
            )
        except TelegramError:
            self.logger.exception("Failed to send document via Telegram")
        except OSError, RuntimeError:
            self.logger.exception("OS error sending document")
        except Exception:
            self.logger.exception("Unexpected error sending document")

    async def _send_text(self, response: str) -> None:
        try:
            await self.application.bot.send_message(
                chat_id=self._chat_id,
                text=response,
                parse_mode="HTML",
            )
        except TelegramError:
            self.logger.exception("Failed to send text via Telegram")
        except OSError, RuntimeError:
            self.logger.exception("OS error sending text")
        except Exception:
            self.logger.exception("Unexpected error sending text")

    async def send(self, message: Message) -> None:
        response = format_message(message)
        if not self.application:
            self.logger.error("Telegram bot is not set up. Cannot send message.")
            return
        if message.type == "photo":
            if not isinstance(response, (bytes, bytearray)):
                self.logger.error("Photo response missing bytes")
                return
            await self._send_photo(message, bytes(response))
        elif message.type == "doc":
            if not isinstance(response, (bytes, bytearray)):
                self.logger.error("Doc response missing bytes")
                return
            await self._send_document(message, bytes(response))
        else:
            self.logger.debug("Periodic Update: Sending HTML message to Telegram.")
            await self._send_text(str(response))


def get_interfaces(request_queue: asyncio.Queue) -> list[MessageInterface]:
    interfaces = []
    settings = get_settings()
    if settings.use_telegram:
        interfaces.append(TelegramInterface(request_queue=request_queue))
    return interfaces
