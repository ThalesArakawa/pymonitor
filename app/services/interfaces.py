from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from settings import get_settings
from functools import cache
import asyncio
from .log import get_logger
from .state_manager import StateManager
import cv2


def format_message(results, subtitle: str = ""):
    html_response = f""
    for result in results:
        if result.ok_status is not None:
            if result.ok_status:
                html_response += f"<b>🟢{result.title}</b>\n{result.content}\n"
            else:
                html_response += f"<b>🔴{result.title}</b>\n{result.content}\n"
        else:
            html_response += f"<b>⚪{result.title}</b>\n{result.content}\n"
    return html_response


class TelegramInterface:
    def __init__(self, state: StateManager):
        self._token = get_settings().telegram.bot_token
        self._chat_id = get_settings().telegram.chat_id
        self.settings = get_settings()
        self.logger = get_logger()
        self.state = state
        self.application = Application.builder().token(self._token).build()
        self.connected = False
        self.photo_mode = get_settings().monitoring.photo_mode

    async def listen(self) -> None:
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

    async def get_status(self, update, context):
        self.logger.debug("Getting Status")
        messages = []
        state = self.state.get_all()
        for _, message in state.items():
            if isinstance(message, dict):
                for _, l2_message in message.items():
                    messages.append(l2_message)
            else:
                messages.append(message)
        html_response = format_message(messages, "Response from system status check:")
        await update.message.reply_html(html_response)

    async def get_log(self, update, context):
        try:
            with open(self.settings.base_path / "app.log", "rb") as f:
                log = f.read()
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            log = None
        if not log:
            await update.message.reply_text("No log available.")
            return
        await update.message.reply_document(log)

    async def get_photo(self, update, context):
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
            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                self.logger.error("Error: Could not encode image.")
                return None

            # Save the captured frame as an image file
            photo = buffer.tobytes()

        else:
            self.logger.error("Error: Failed to capture frame.")

        if not photo:
            await update.message.reply_text("No photo available.")
            return
        await update.message.reply_photo(photo)

    async def send_message(self, results):
        html_response = format_message(results, "Periodic Update:")
        if self.application:
            self.logger.debug(f"Periodic Update: Sending HTML message to Telegram.")
            await self.application.bot.send_message(
                chat_id=self._chat_id,
                text=html_response,
                parse_mode="HTML",
            )
        else:
            self.logger.error("Telegram bot is not set up. Cannot send message.")


def get_interfaces(state: dict) -> dict:
    return {
        "telegram": TelegramInterface(state=state),
    }
