from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, Field
from typing import Literal, Optional
from functools import cache
import os
import logging
import logging.config
import sys
from pathlib import Path

type Env = Literal['test', 'dev', 'prod']
type LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
type MonitoringMode = Literal['active', 'passive', 'both']

class TobiiSettings(BaseSettings):
    optikey_exe_name: str = Field("OptiKey.exe", description="Name of Optikey Executable (.exe)")
    optikey_path: str = Field("./OptiKey.exe", description="Full path to Executable")
    eyex_engine_exe_name: str = Field("Tobii.EyeX.Engine.exe", description="Name of Tobii Engine Service Executable (.exe)")
    eyex_interaction_exe_name: str = Field("Tobii.EyeX.Interaction.exe", description="Name of Tobii Engine Interaction Executable (.exe)")
    service_exe_name: str = Field("Tobii.Service.exe", description="Name of Tobii Service Executable (.exe)")
    service_name: str = Field("Tobii Service", description="Name of Tobii Service")
    generic_name: str = Field("TobiiGeneric", description="Name of Tobii Generic Service")
    eyetracker_name: str = Field("TobiilS5LEYETRACKER5", description="Name of Tobii Eyetracker Service")


class TelegramSettings(BaseSettings):
    bot_token: str
    chat_id: str


class MonitoringSettings(BaseSettings):
    photo_mode: bool = Field(False, description="Enable photo monitoring")
    mode: MonitoringMode = Field('both', description="Monitoring Mode")  # active, passive, or both   
    check_interval: int = Field(5, description="Interval in seconds to check system status")


class RemoteAccessSettings(BaseSettings):
    anydesk_exe_name: str = Field("AnyDesk.exe", description="Name of AnyDesk Executable (.exe)")
    anydesk_path: str = Field("./AnyDesk.exe", description="Full path to Executable")


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
    tobii: TobiiSettings = TobiiSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    remote_access: RemoteAccessSettings = RemoteAccessSettings()
    log_level: LogLevel = Field('DEBUG', frozen=True)
    log_format: Optional[str] = Field('%(asctime)s | %(name)s | %(levelname)s | %(message)s', frozen=True)
    log_date_format: Optional[str] = Field('%Y-%m-%d %H:%M:%S', frozen=True)
    
    @computed_field
    @property
    def base_path(self) -> str:
        if getattr(sys, 'frozen', False):
            base_path = Path(os.path.dirname(sys.executable))
        else:
            # If running as a python script, get the path of the script
            base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        return base_path

    @computed_field
    @property
    def assets_path(self) -> Path:
        return self.base_path.parent / "assets/"
    
    @computed_field
    @property
    def root_path(self) -> str:
        return os.path.dirname(self.base_path)


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
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'app.log',
                    'formatter': 'default',
                    'level': self.log_level,
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8',
                },
            },
            'root': {
                'level': self.log_level,
                'handlers': ['file', 'stdout'],
            },
        }

    def model_post_init(self, context):
        logging.config.dictConfig(self.logging_config)
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('httpcore').setLevel(logging.INFO)
        logging.getLogger('telegram').setLevel(logging.INFO)
        logging.getLogger('asyncio').setLevel(logging.INFO)
        logging.getLogger('httpx').setLevel(logging.INFO)
    

@cache
def get_settings() -> AppSettings:
    return AppSettings()
