import asyncio

from app.services.database import StateManager
from app.services.log import get_logger
from app.services.messenger import MessengerService
from app.services.metrics import MetricsService
from app.services.pyagent import PyAgent
from app.services.pymonitor import PyMonitor
from app.settings import get_settings


async def main() -> None:
    settings = get_settings()
    logger = get_logger()
    logger.info(f"Configuração: {settings}")

    pymonitor = PyMonitor(
        metric_collector=MetricsService(settings=settings, logger=logger),
        agent=PyAgent(messenger=MessengerService()),
        event_queue=asyncio.Queue(),
        database_connector=StateManager(),
    )
    await pymonitor.start()


if __name__ == "__main__":
    asyncio.run(main())
