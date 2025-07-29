import logging.config
from settings import get_settings

LOG_NAME = 'pymonitor'

def get_logger(log_level = logging.DEBUG) -> logging.Logger:
    
    settings = get_settings()
    logging.config.dictConfig(settings.logging_config)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    return logging.getLogger(LOG_NAME)