"""Unit-scoped fixtures for services tests."""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.models import Event
from app.services.database import StateManager
from app.services.metrics import MetricsService
from app.settings import AppSettings


@pytest.fixture
def event_queue() -> asyncio.Queue[Event]:
    """Provide an isolated asyncio queue for event emission."""
    return asyncio.Queue()


@pytest.fixture
def state_manager() -> StateManager:
    """Provide a fresh in-memory StateManager."""
    return StateManager()


@pytest.fixture
def metrics_service(
    app_settings: AppSettings, mock_logger: MagicMock
) -> MetricsService:
    """Provide MetricsService with injected settings and logger (DIP)."""
    return MetricsService(settings=app_settings, logger=mock_logger)


@pytest.fixture
def metrics_service_with_queue(
    metrics_service: MetricsService,
    event_queue: asyncio.Queue[Event],
    state_manager: StateManager,
) -> MetricsService:
    """Provide MetricsService with queue and state tracker wired via setters."""
    metrics_service.set_event_queue(event_queue)
    metrics_service.set_state_tracker(state_manager)
    return metrics_service
