from .log import get_logger
import asyncio
from .interfaces import get_interfaces


class MessengerService:
    def __init__(self, queue: asyncio.Queue, state: dict):
        self.logger = get_logger()
        self.interfaces = get_interfaces(state=state)
        self.queue = queue
        self.state = state

    async def sender(self):
        while True:
            # Trava aqui até que um produtor coloque algo na fila
            evento = await self.queue.get()

            for interface in self.interfaces.values():
                try:
                    await interface.send_message([evento])
                except Exception as e:
                    self.logger.error(
                        f"Failed to send message via {interface.__class__.__name__}: {e}"
                    )
                    # Se der erro de rede, você poderia recolocar o evento na fila para tentar depois
                finally:
                    # Avisa a fila que o processamento deste item terminou
                    self.queue.task_done()

    async def listener(self):
        await asyncio.gather(*[interface.listen() for interface in self.interfaces.values()])

    async def start(self):
        sender_task = asyncio.create_task(self.sender())
        listener_task = asyncio.create_task(self.listener())
        await asyncio.gather(sender_task, listener_task)
