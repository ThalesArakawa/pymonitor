from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from settings import AppSettings
import requests
import logging

class TelegramBot:
    def __init__(self, settings: AppSettings, logger: logging.Logger):
        self.token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.updater = None
        self.dispatcher = None
        self.logger = logger

    def setup(self):
        self.updater = Updater(self.token)
        self.dispatcher = self.updater.dispatcher

    def send_message(self, text: str):
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        data = {'chat_id': self.chat_id, 'text': text}
        try:
            requests.post(url, data=data)
        except requests.RequestException as e:
            self.logger.error(f"Failed to send message: {e}")

    def start(self):
        self.updater.start_polling()