import asyncio

from app.services.log import get_logger
from app.services.pymonitor import PyMonitor
from app.settings import get_settings


async def main() -> None:
    settings = get_settings()
    logger = get_logger()
    logger.info(f"Configuração: {settings}")
    pymonitor = PyMonitor()
    await pymonitor.start()


if __name__ == "__main__":
    asyncio.run(main())
