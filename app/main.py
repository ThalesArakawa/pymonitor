from services.pyagent import PyAgent
from services.log import get_logger
from settings import get_settings
import asyncio


def start_up() -> None:
    settings = get_settings()
    logger = get_logger(settings.log_level)

    return settings, logger


async def main() -> None:
    pyagent = PyAgent()

    await asyncio.gather(
        pyagent.active_monitoring(),
        # pyagent.passive_monitoring()
    )
    
    # logger.info("Starting Windows Monitor...")
    # while True:
    #     time.sleep(settings.check_interval)
    #     logger.debug("Checking system status...")
    #     monitor.system_status()


if __name__ == "__main__":
    asyncio.run(main())
