from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from telegram import Update


class Message(BaseModel):
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    type: str = ""
    content: str = Field(..., description="Content of the message")
    byte_content: bytes | None = b""
    recipient: Any | Update | None = None
