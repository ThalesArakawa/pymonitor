import threading
from abc import ABC, abstractmethod

from ..models import Event


class DataBaseConnector(ABC):
    @abstractmethod
    def update_state(self, key: str, content: Event) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Event:
        pass

    @abstractmethod
    def get_all(self) -> dict[str, Event]:
        pass


class StateManager(DataBaseConnector):
    def __init__(self) -> None:
        self.state: dict[str, Event] = {}
        self._lock = threading.Lock()

    def update_state(self, key: str, content: Event) -> None:
        with self._lock:
            self.state[key] = content

    def get(self, key: str) -> Event:
        with self._lock:
            content = Event(message="", status=None)
            return self.state.get(key, content)

    def get_all(self) -> dict[str, Event]:
        with self._lock:
            return dict(self.state)
