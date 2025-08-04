from .messenger import get_messenger
from settings import get_settings
from .monitor import get_monitor
import asyncio
from .log import get_logger


class PyAgent:
    def __init__(self):
        self.monitor = get_monitor()
        self.messager = get_messenger()
        self.settings = get_settings()
        self.logger = get_logger()

    async def active_monitoring(self):
        self.logger.debug("Active monitoring started.")
        while True:
            await asyncio.sleep(5)
            results = self.monitor.system_status()
            for result in results:
                if result.ok_status is not None:
                    self.logger.info(f"{result.title}: {result.content}")
                else:
                    self.logger.warning(f"{result.title}: {result.content}")
            
            await self.messager.send_message(results)
            self.logger.debug("Active monitoring completed. Waiting for next cycle.")
        

    async def passive_monitoring(self):
        await self.messager.listen()