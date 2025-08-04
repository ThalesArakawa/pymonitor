from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, Field
from typing import Literal, Optional
from functools import cache

type Env = Literal['test', 'dev', 'prod']
type LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
type MonitoringMode = Literal['active', 'passive', 'both']

class TelegramSettings(BaseSettings):
    bot_token: str
    chat_id: str


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False,
        extra='ignore',
        env_prefix='PYMONITOR__',
        env_nested_delimiter='__',
        nested_model_default_partial_update=True,
    )

    env: Env = 'test'
    telegram: TelegramSettings

    log_level: LogLevel = Field('DEBUG', frozen=True)
    log_format: Optional[str] = Field('%(asctime)s - %(name)s - %(levelname)s - %(message)s', frozen=True)
    log_date_format: Optional[str] = Field('%Y-%m-%d %H:%M:%S', frozen=True)
    check_interval: Optional[int] = Field(300, description="Interval in seconds to check system status")

    @computed_field
    @property
    def logging_config(self) -> dict:
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': self.log_format,
                    'datefmt': self.log_date_format,
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'level': self.log_level,
                    'stream': 'ext://sys.stderr',
                },
                'stdout': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                    'formatter': 'default',
                    'level': self.log_level,
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': 'app.log',
                    'formatter': 'default',
                    'level': self.log_level,
                },
            },
            'root': {
                'level': self.log_level,
                'handlers': ['file', 'stdout'],
            },
        }

@cache
def get_settings() -> AppSettings:
    return AppSettings()