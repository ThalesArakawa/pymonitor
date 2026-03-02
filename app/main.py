from services.pyagent import PyAgent
import asyncio
from services.log import get_logger
from settings import get_settings
async def main() -> None:
    settings = get_settings()
    logger = get_logger()
    logger.debug(f"Caminho dos áudios: {settings.assets_path}")
    pyagent = PyAgent()
    await pyagent.start()

if __name__ == "__main__":
    asyncio.run(main())
