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
    ):
        self.metric_collector = metric_collector
        self.event_queue = event_queue
        self.agent = agent
        self.database_connector = database_connector
        self.tasks = []

        self._initialize()

    def _initialize(self):
        self.metric_collector.set_event_queue(self.event_queue)
        self.metric_collector.set_state_tracker(self.database_connector)
        self.tasks.append(asyncio.create_task(self.metric_collector.start()))

        self.agent.set_event_queue(self.event_queue)
        self.agent.set_state_tracker(self.database_connector)
        self.tasks.append(asyncio.create_task(self.agent.start()))

    async def start(self):
        await asyncio.gather(*self.tasks)
