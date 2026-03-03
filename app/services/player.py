from .log import get_logger
import asyncio
from playsound3 import playsound
from ..settings import get_settings


class AudioService:
    def __init__(self, queue: asyncio.Queue, state: dict):
        self.logger = get_logger()
        self.settings = get_settings()
        self.queue = queue
        self.state = state

    async def play(self, evento):
        self.logger.info("Playing Audio")
        if evento == "battery_connected":
            audio = self.settings.assets_path / "connected.mp3"
        elif evento == "battery_disconnected":
            audio = self.settings.assets_path / "disconnected.mp3"
        await asyncio.to_thread(playsound, audio, False)

    async def player(self):
        while True:
            # Trava aqui até que um produtor coloque algo na fila
            evento = await self.queue.get()

            try:
                await self.play(evento)
            except Exception as e:
                self.logger.error(f"Failed to play audio: {e}")
                # Se der erro de rede, você poderia recolocar o evento na fila para tentar depois
            finally:
                # Avisa a fila que o processamento deste item terminou
                self.queue.task_done()

    async def start(self):
        player_task = asyncio.create_task(self.player())
        await asyncio.gather(player_task)
