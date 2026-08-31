from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Request(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    request_id: str | None = None
    message: Any
    timestamp: datetime | None = None
    update: Any