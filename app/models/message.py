from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from telegram import Update


class Message(BaseModel):
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    type: str = ""
    content: str = Field(..., description="Content of the message")
    byte_content: Optional[bytes] = b''
    recipient: Optional[Any | Update] = None
