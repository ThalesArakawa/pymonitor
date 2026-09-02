"""Global fixtures reused across unit and integration tests."""

import logging
from unittest.mock import MagicMock

import pytest

from app.settings import AppSettings


@pytest.fixture
def mock_logger() -> MagicMock:
    """Provide a mocked logger with common methods."""
    logger = MagicMock(spec=logging.Logger)
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def app_settings() -> AppSettings:
    """Provide deterministic AppSettings for tests."""
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
