import asyncio

from .database import DataBaseConnector
from .metrics import MetricsService
from .pyagent import PyAgent


class PyMonitor:
    def __init__(
        self,
        metric_collector: MetricsService,
        agent: PyAgent,
        event_queue: asyncio.Queue,
        database_connector: DataBaseConnector,
    ) -> None:
        self.metric_collector = metric_collector
        self.event_queue: asyncio.Queue = event_queue
        self.agent = agent
        self.database_connector = database_connector
        self.tasks: list[asyncio.Task[None]] = []

    def _configure(self) -> None:
        self.metric_collector.set_event_queue(self.event_queue)
        self.metric_collector.set_state_tracker(self.database_connector)
        self.agent.set_event_queue(self.event_queue)
        self.agent.set_state_tracker(self.database_connector)

    async def start(self) -> None:
        self._configure()
        self.tasks = [
            asyncio.create_task(self.metric_collector.start()),
            asyncio.create_task(self.agent.start()),
        ]
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            for task in self.tasks:
                task.cancel()
            raise
