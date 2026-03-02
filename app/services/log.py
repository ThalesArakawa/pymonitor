from functools import cache
import logging

LOG_NAME = 'pymonitor'

@cache
def get_logger() -> logging.Logger:
    return logging.getLogger(LOG_NAME)
    