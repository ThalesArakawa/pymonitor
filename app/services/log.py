import logging.config
from settings import get_settings
from functools import cache

LOG_NAME = 'pymonitor'

@cache
def get_logger(log_level = logging.DEBUG) -> logging.Logger:
    
    settings = get_settings()
    logging.config.dictConfig(settings.logging_config)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('httpcore').setLevel(logging.INFO)
    logging.getLogger('telegram').setLevel(logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.INFO)
    return logging.getLogger(LOG_NAME)
    