import time
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from services.monitor import MonitoringService
from services.telegram_interface import TelegramInterface
from services.log import get_logger
from settings import get_settings
import asyncio


def start_up() -> None:
    settings = get_settings()
    logger = get_logger(settings.log_level)

    return settings, logger


async def main() -> None:
    settings, logger = start_up()

    monitor = MonitoringService(
        logger=logger,
    )

    telegram_bot = TelegramInterface(
        token=settings.telegram.bot_token,
        chat_id=settings.telegram.chat_id,
        monitor=monitor,
        logger=logger,
    )

    logger.info("Available Features to Monitoring...")
    monitor.setup()
    
    telegram_bot.setup()
    await telegram_bot.start()
    await asyncio.gather(
        telegram_bot.application.updater.start_polling(),
        telegram_bot.send_html_message("Periodic Update"),
    )
    
    # logger.info("Starting Windows Monitor...")
    # while True:
    #     time.sleep(settings.check_interval)
    #     logger.debug("Checking system status...")
    #     monitor.system_status()


if __name__ == "__main__":
    asyncio.run(main())
