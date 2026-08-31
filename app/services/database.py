from abc import ABC

from ..models import Event


class DataBaseConnector(ABC):

    @classmethod
    def update_state(self, key, content):
        pass

    @classmethod
    def get(self, key):
        pass

    @classmethod
    def get_all(self):
        pass


class StateManager(DataBaseConnector):
    def __init__(self):
        self.state = {}

    def update_state(self, key, content):
        self.state[key] = content

    def get(self, key):
        content = Event(message="",status=None)
        return self.state.get(key, content)

    def get_all(self):
        return self.state
