from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from settings import AppSettings
import requests

class TelegramBot:
    def __init__(self, settings: AppSettings):
        self.token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.updater = None
        self.dispatcher = None

    def setup(self):
        self.updater = Updater(self.token)
        self.dispatcher = self.updater.dispatcher

    def send_message(self, text: str):
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        data = {'chat_id': self.chat_id, 'text': text}
        requests.post(url, data=data)

    def start(self):
        self.updater.start_polling()