import win32con
import win32gui
import win32api
import win32ts
import requests
import subprocess
import time
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from services.monitor import WindowsMonitor
from services.telegram_bot import TelegramBot
from settings import get_settings

# def send_telegram_message(text):
#     url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
#     data = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
#     requests.post(url, data=data)

def main():
    settings = get_settings()
    telegram_bot = TelegramBot(settings=settings)
    monitor = WindowsMonitor(telegram_bot=telegram_bot)
    while True:
        time.sleep(settings.check_interval)
        print("Checking system status...")
        monitor.system_status()

if __name__ == "__main__":
    main()

