from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

type EventStatus = Literal[True, False, None]


class Event(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    event_id: str | None = None
    message: str
    resource_name: str | None = None
    status: EventStatus
    value: Any | None = None
    timestamp: datetime | None = None
