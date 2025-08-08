from pydantic import BaseModel, Field
from typing import List
import datetime


type ListMonitoringMessage = List['MonitoringMessage']


class MonitoringMessage(BaseModel):
    """
    Represents a message to be sent to the Telegram bot.
    """
    title: str = Field(..., description="Title of the message")
    content: str = Field(..., description="Content of the message")
    ok_status: bool | None = Field(..., description="Status of the monitoring check (True for OK/False for NOT OK)")
    value: str = None