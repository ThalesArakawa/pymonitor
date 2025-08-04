from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import logging
from .monitor import MonitoringService
from settings import get_settings
import asyncio




class TelegramInterface:
    def __init__(self, token, chat_id, monitor: MonitoringService, logger: logging.Logger):
        self.token = token
        self.chat_id = chat_id
        self.logger = logger
        self.application = None
        self.monitor = monitor
        self.settings = get_settings()

    def setup(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("status", self.get_status))

    async def start(self):
        await self.application.initialize()
        await self.application.start()
      
    async def get_status(self, update, context):
        results = self.monitor.system_status()
        html_response = "<b>System Status:</b>\n<b>Response Update</b>\n\n"
        for result in results:
            if result.ok_status is not None:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
            else:
                html_response += f"<b>{result.title}</b>\n{result.content}\n"
        
        await update.message.reply_html(html_response)
    
    async def send_html_message(self,title: str = None):
        while True:
            await asyncio.sleep(self.settings.check_interval)
            results = self.monitor.system_status()
            html_response = f"<b>System Status:</b>\n<b>{title}</b>\n\n"
            c = 0
            for result in results:
                if result.ok_status is not None:
                    html_response += f"<b>{result.title}</b>\n{result.content}\n"
                else:
                    html_response += f"<b>{result.title}</b>\n{result.content}\n"
            if self.application:
                self.logger.debug(f"Periodic Update: Sending HTML message to Telegram.{c} Periodic Update: Sending HTML message to Telegram.")
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=html_response,
                    parse_mode='HTML',
                )
            else:
                self.logger.error("Telegram bot is not set up. Cannot send message.")