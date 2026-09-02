import logging
from functools import cache

LOG_NAME = "pymonitor"


@cache
def get_logger() -> logging.Logger:
    return logging.getLogger(LOG_NAME)
