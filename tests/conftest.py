import asyncio
import logging
from unittest.mock import MagicMock

import pytest

from app.models import Event
from app.services.database import StateManager
from app.services.metrics import MetricsService
from app.settings import AppSettings


@pytest.fixture
def mock_logger() -> MagicMock:
    logger = MagicMock(spec=logging.Logger)
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def app_settings() -> AppSettings:
    return AppSettings(
        env="test",
        use_telegram=False,
        use_alarm_sound=False,
        telegram={"bot_token": "dummy", "chat_id": "123"},
        monitoring={"check_interval": 10, "photo_mode": False},
        tobii={
            "optikey_exe_name": "OptiKey.exe",
            "optikey_path": "./OptiKey.exe",
            "eyex_engine_exe_name": "Tobii.EyeX.Engine.exe",
            "eyex_interaction_exe_name": "Tobii.EyeX.Interaction.exe",
            "service_exe_name": "Tobii.Service.exe",
            "service_name": "Tobii Service",
            "generic_name": "TobiiGeneric",
            "eyetracker_name": "TobiilS5LEYETRACKER5",
        },
        remote_access={
            "anydesk_exe_name": "AnyDesk.exe",
            "anydesk_path": "./AnyDesk.exe",
        },
        alarm={"interval": 60},
    )


@pytest.fixture
def event_queue() -> asyncio.Queue[Event]:
    return asyncio.Queue()


@pytest.fixture
def state_manager() -> StateManager:
    return StateManager()


@pytest.fixture
def metrics_service(
    app_settings: AppSettings, mock_logger: MagicMock
) -> MetricsService:
    return MetricsService(settings=app_settings, logger=mock_logger)


@pytest.fixture
def metrics_service_with_queue(
    metrics_service: MetricsService,
    event_queue: asyncio.Queue[Event],
    state_manager: StateManager,
) -> MetricsService:
    metrics_service.set_event_queue(event_queue)
    metrics_service.set_state_tracker(state_manager)
    return metrics_service
