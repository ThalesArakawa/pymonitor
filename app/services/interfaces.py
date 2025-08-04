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
from .monitor import get_monitor
from .log import get_logger

class TelegramInterface:
    def __init__(self):
        self._token = get_settings().telegram.bot_token
        self._chat_id = get_settings().telegram.chat_id
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.application = Application.builder().token(self._token).build()

    async def start(self) -> None:
        self.application.add_handler(CommandHandler("status", self.get_status))
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
      
    async def get_status(self, update, context):
        results = self.monitor.system_status()
        html_response = "<b>System Status:</b>\n<b>Response Update</b>\n\n"
        for result in results:
            if result.ok_status is not None:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
            else:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
        
        await update.message.reply_html(html_response)
    
    async def send_message(self, results):
        html_response = f"<b>System Status:</b>\n\n"
        c = 0
        for result in results:
            if result.ok_status is not None:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
            else:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
        if self.application:
            self.logger.debug(f"Periodic Update: Sending HTML message to Telegram.{c} Periodic Update: Sending HTML message to Telegram.")
            await self.application.bot.send_message(
                chat_id=self._chat_id,
                text=html_response,
                parse_mode='HTML',
            )
        else:
            self.logger.error("Telegram bot is not set up. Cannot send message.")

@cache
def get_interfaces() -> dict:
    return {
        'telegram': TelegramInterface(),
    }