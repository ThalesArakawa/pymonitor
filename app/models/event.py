from pydantic import BaseModel, ConfigDict
from typing import Literal, Any, Optional
from datetime import datetime

type EventStatus = Literal[True, False, None]

class Event(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    event_id: Optional[str | None] = None
    message: str
    status: EventStatus
    value: Optional[Any] = None
    timestamp: Optional[datetime | None] = None