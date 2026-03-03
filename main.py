from app.services.pymonitor import PyMonitor
from app.services.log import get_logger
from app.settings import get_settings

import asyncio

async def main() -> None:
    settings = get_settings()
    logger = get_logger()
    logger.debug(f"Caminho dos áudios: {settings.assets_path}")
    pymonitor = PyMonitor()
    await pymonitor.start()

if __name__ == "__main__":
    asyncio.run(main())
