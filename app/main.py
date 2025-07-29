import time
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from services.monitor import WindowsMonitor
from services.telegram_bot import TelegramBot
from services.log import get_logger
from settings import get_settings

def main():
    settings = get_settings()
    logger = get_logger(settings.log_level)
    telegram_bot = TelegramBot(settings=settings, logger=logger)
    monitor = WindowsMonitor(telegram_bot=telegram_bot, logger=logger)
    logger.info("Starting Windows Monitor...")
    while True:
        time.sleep(settings.check_interval)
        logger.debug("Checking system status...")
        monitor.system_status()

if __name__ == "__main__":
    main()

