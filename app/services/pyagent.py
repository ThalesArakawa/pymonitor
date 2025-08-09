from .messenger import get_messenger
from settings import get_settings
from .monitor import get_monitor
import asyncio
from .log import get_logger
from .custom_types import ListMonitoringMessage
from playsound import playsound
from pathlib import Path
import logging

async def diff_states(result: ListMonitoringMessage, old_result: ListMonitoringMessage | None, logger: logging.Logger)->bool:
    settings = get_settings()
    status = False
    if old_result is None:
        return True
    for msg, old_msg in zip(result, old_result if old_result else []):
        if msg != old_msg:
            # return True
            status = True | status
            if msg.title == 'System Locked Status' and msg.ok_status == False:
                try:
                    logger.debug(f"Playing sound {Path(settings.assets_path)}")
                    await playsound(str(Path(settings.assets_path) / 'disconnected.mp3'), block=False)
                except Exception as e:
                    logger.error(f"Error playing sound {str(Path(settings.root_path) / 'assets' / 'disconnected.mp3')}: {e}")
            if msg.title == 'System Locked Status' and msg.ok_status == True:
                try:
                    logger.debug(f"Playing sound {Path(settings.assets_path)}")
                    await playsound(str(Path(settings.assets_path) / 'connected.mp3'), block=False)
                except Exception as e:
                    logger.error(f"Error playing sound{str(Path(settings.root_path) / 'assets' / 'disconnected.mp3')}: {e}")
            # if msg.title == 'System Locked Status' and msg.ok_status == False:
            #     playsound(Path(settings.assets_path) / 'Por favor, reco.mp3')
    if status:
        return True
    return False



class PyAgent:
    def __init__(self):
        self.monitor = get_monitor()
        self.messenger = get_messenger()
        self.settings = get_settings()
        self.logger = get_logger()
        self.monitor_result = None

    async def start(self):
        await asyncio.gather(
            self.active_monitoring(),
            self.passive_monitoring()
        )

    async def active_monitoring(self):
        self.logger.debug("Active monitoring started.")
        while True:
            result = self.monitor.system_status()
            send = await diff_states(result, self.monitor_result, self.logger)
            if send:
                self.monitor_result = result
                await self.messenger.send_message(result)
            self.logger.debug("Active monitoring completed. Waiting for next cycle.")
            await asyncio.sleep(5)
            
        

    async def passive_monitoring(self):
        await self.messenger.listen()