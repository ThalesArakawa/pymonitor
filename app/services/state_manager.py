from .custom_types import MonitoringMessage


class StateManager:
    def __init__(self):
        self.state = {}

    def update_state(self, key, content):
        self.state[key] = content

    def get(self, key):
        content = MonitoringMessage(
            title="",
            content="",
            ok_status=None,
        )
        if key == "tobii_status" and self.state.get("tobii_status", None) is None:
            content = {}

        return self.state.get(key, content)

    def get_all(self):
        return self.state
