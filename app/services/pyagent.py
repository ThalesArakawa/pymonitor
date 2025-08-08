from .messenger import get_messenger
from settings import get_settings
from .monitor import get_monitor
import asyncio
from .log import get_logger
from .custom_types import ListMonitoringMessage
from playsound import playsound
from pathlib import Path

def diff_states(result: ListMonitoringMessage, old_result: ListMonitoringMessage | None)->bool:
    settings = get_settings()
    status = False
    if old_result is None:
        return True
    for msg, old_msg in zip(result, old_result if old_result else []):
        print(f"Comparing: {msg} with {old_msg}")
        if msg != old_msg:
            # return True
            status = True | status
            if msg.title == 'Battery Status' and msg.ok_status == False:
                playsound(Path(settings.assets_path) / 'Por favor, reco.mp3')
            if msg.title == 'Battery Status' and msg.ok_status == True:
                playsound(Path(settings.assets_path) / 'Carregador cone.mp3')
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
            send = diff_states(result, self.monitor_result)
            if send:
                self.monitor_result = result
                await self.messenger.send_message(result)
            self.logger.debug("Active monitoring completed. Waiting for next cycle.")
            await asyncio.sleep(5)
            
        

    async def passive_monitoring(self):
        await self.messenger.listen()