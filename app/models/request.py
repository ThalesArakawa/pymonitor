from pydantic import BaseModel, ConfigDict
from typing import Literal, Any, Optional
from datetime import datetime


class Request(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    request_id: Optional[str | None] = None
    message: Any
    timestamp: Optional[datetime | None] = None
    update: Any