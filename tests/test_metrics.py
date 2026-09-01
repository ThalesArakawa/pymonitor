import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import psutil
import pytest

from app.models import Event
from app.services.metrics import (
    BatteryLookupError,
    MetricsService,
    NetworkLookupError,
    ProcessLookupError,
    ServiceLookupError,
    WMIUnavailableError,
    _collect_and_emit,
    _collect_process_names,
    _format_tobii_summary,
    _get_battery_stats,
    _get_network_states,
    _is_service_running,
    _query_wmi_devices,
    _resolve_interval,
)

# ---------------------------------------------------------------------------
# Helpers — pure blocking units (mock external psutil/wmi only)
# ---------------------------------------------------------------------------


def test_collect_process_names_with_valid_iter_returns_set():
    # Arrange
    proc_a = MagicMock()
    proc_a.info = {"name": "OptiKey.exe"}
    proc_b = MagicMock()
    proc_b.info = {"name": "AnyDesk.exe"}
    proc_c = MagicMock()
    proc_c.info = {"name": None}

    with patch(
        "app.services.metrics.psutil.process_iter",
        return_value=[proc_a, proc_b, proc_c],
    ):
        # Act
        result = _collect_process_names()

        # Assert
        assert result == {"OptiKey.exe", "AnyDesk.exe"}


def test_collect_process_names_with_access_denied_raises_process_lookup_error():
    # Arrange
    with patch(
        "app.services.metrics.psutil.process_iter",
        side_effect=psutil.AccessDenied(pid=123),
    ):
        # Act / Assert
        with pytest.raises(ProcessLookupError):
            _collect_process_names()


def test_collect_process_names_with_os_error_raises_process_lookup_error():
    # Arrange
    with patch("app.services.metrics.psutil.process_iter", side_effect=OSError("fail")):
        # Act / Assert
        with pytest.raises(ProcessLookupError):
            _collect_process_names()


def test_get_network_states_with_valid_stats_returns_tuple():
    # Arrange
    eth = MagicMock(isup=True)
    wifi = MagicMock(isup=False)
    fake_stats = {"Ethernet": eth, "Wi-Fi": wifi}

    with patch("app.services.metrics.psutil.net_if_stats", return_value=fake_stats):
        # Act
        ethernet, wifi_state = _get_network_states()

        # Assert
        assert ethernet is eth
        assert wifi_state is wifi


def test_get_network_states_with_os_error_raises_network_lookup_error():
    # Arrange
    with patch("app.services.metrics.psutil.net_if_stats", side_effect=OSError("down")):
        # Act / Assert
        with pytest.raises(NetworkLookupError):
            _get_network_states()


def test_get_battery_stats_with_valid_data_returns_stats():
    # Arrange
    fake_battery = MagicMock(power_plugged=True, percent=80)

    with patch(
        "app.services.metrics.psutil.sensors_battery", return_value=fake_battery
    ):
        # Act
        result = _get_battery_stats()

        # Assert
        assert result is fake_battery


def test_get_battery_stats_with_os_error_raises_battery_lookup_error():
    # Arrange
    with patch(
        "app.services.metrics.psutil.sensors_battery", side_effect=OSError("no battery")
    ):
        # Act / Assert
        with pytest.raises(BatteryLookupError):
            _get_battery_stats()


def test_get_battery_stats_with_none_returns_none():
    # Arrange
    with patch("app.services.metrics.psutil.sensors_battery", return_value=None):
        # Act
        result = _get_battery_stats()

        # Assert
        assert result is None


def test_query_wmi_devices_when_module_missing_raises_wmi_unavailable():
    # Arrange
    with patch("app.services.metrics.wmi_module", None):
        # Act / Assert
        with pytest.raises(WMIUnavailableError, match="unavailable on this platform"):
            _query_wmi_devices()


def test_query_wmi_devices_with_valid_devices_returns_list():
    # Arrange
    device = MagicMock()
    device.Name = "Tobii Eye Tracker 5"
    fake_conn = MagicMock()
    fake_conn.Win32_PnPEntity.return_value = [device]
    fake_wmi = MagicMock()
    fake_wmi.WMI.return_value = fake_conn

    with patch("app.services.metrics.wmi_module", fake_wmi):
        # Act
        result = _query_wmi_devices()

        # Assert
        assert result == [device]
        fake_wmi.WMI.assert_called_once()
        fake_conn.Win32_PnPEntity.assert_called_once()


def test_query_wmi_devices_with_os_error_raises_wmi_unavailable():
    # Arrange
    fake_wmi = MagicMock()
    fake_wmi.WMI.side_effect = OSError("COM failed")

    with patch("app.services.metrics.wmi_module", fake_wmi):
        # Act / Assert
        with pytest.raises(WMIUnavailableError):
            _query_wmi_devices()


def test_is_service_running_with_running_service_returns_true():
    # Arrange
    fake_service = MagicMock()
    fake_service.as_dict.return_value = {"status": "running"}

    with patch(
        "app.services.metrics.psutil.win_service_get",
        return_value=fake_service,
        create=True,
    ):
        # Act
        result = _is_service_running("Tobii Service")

        # Assert
        assert result is True


def test_is_service_running_with_stopped_service_returns_false():
    # Arrange
    fake_service = MagicMock()
    fake_service.as_dict.return_value = {"status": "stopped"}

    with patch(
        "app.services.metrics.psutil.win_service_get",
        return_value=fake_service,
        create=True,
    ):
        # Act
        result = _is_service_running("Tobii Service")

        # Assert
        assert result is False


def test_is_service_running_with_no_such_process_returns_false():
    # Arrange
    with patch(
        "app.services.metrics.psutil.win_service_get",
        side_effect=psutil.NoSuchProcess(pid=999),
        create=True,
    ):
        # Act
        result = _is_service_running("Missing Service")

        # Assert
        assert result is False


def test_is_service_running_with_os_error_raises_service_lookup_error():
    # Arrange
    with patch(
        "app.services.metrics.psutil.win_service_get",
        side_effect=OSError("scm"),
        create=True,
    ):
        # Act / Assert
        with pytest.raises(ServiceLookupError):
            _is_service_running("Tobii Service")


def test_format_tobii_summary_with_all_up_returns_true_and_message():
    # Arrange
    states = {"Tobii Service": True, "TobiiGeneric": True}

    # Act
    message, all_up = _format_tobii_summary(states)

    # Assert
    assert all_up is True
    assert "Tobii Service UP" in message
    assert "TobiiGeneric UP" in message


def test_format_tobii_summary_with_one_down_returns_false():
    # Arrange
    states = {"Tobii Service": True, "TobiiGeneric": False}

    # Act
    message, all_up = _format_tobii_summary(states)

    # Assert
    assert all_up is False
    assert "DOWN" in message


def test_resolve_interval_with_none_returns_fallback():
    # Arrange
    configured = None
    fallback = 10.0

    # Act
    result = _resolve_interval(configured, fallback)

    # Assert
    assert result == 10.0


def test_resolve_interval_with_value_returns_configured():
    # Arrange
    configured = 60.0
    fallback = 10.0

    # Act
    result = _resolve_interval(configured, fallback)

    # Assert
    assert result == 60.0


# ---------------------------------------------------------------------------
# _collect_and_emit — asyncio boundary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_and_emit_with_status_change_enqueues_event():
    # Arrange
    queue = asyncio.Queue()
    tracker = MagicMock()
    tracker.get.return_value = Event(message="", status=True)
    logger = MagicMock()
    new_event = Event(message="changed", status=False)

    async def fake_func(self_obj, *args, **kwargs):
        return new_event

    # Act
    await _collect_and_emit(tracker, queue, logger, "Optikey", fake_func, None, (), {})

    # Assert
    assert queue.qsize() == 1
    emitted = await queue.get()
    assert emitted is new_event
    assert emitted.resource_name == "Optikey"
    assert emitted.timestamp is not None
    assert emitted.event_id is not None
    tracker.update_state.assert_called_once_with(key="Optikey", content=new_event)
    logger.info.assert_called_once_with("Enviando evento...")


@pytest.mark.asyncio
async def test_collect_and_emit_with_no_status_change_does_not_enqueue():
    # Arrange
    queue = asyncio.Queue()
    tracker = MagicMock()
    tracker.get.return_value = Event(message="same", status=True)
    logger = MagicMock()
    same_event = Event(message="same", status=True)

    async def fake_func(self_obj, *args, **kwargs):
        return same_event

    # Act
    await _collect_and_emit(tracker, queue, logger, "Optikey", fake_func, None, (), {})

    # Assert
    assert queue.empty()
    tracker.update_state.assert_not_called()


@pytest.mark.asyncio
async def test_collect_and_emit_with_process_lookup_error_logs_and_continues():
    # Arrange
    queue = asyncio.Queue()
    tracker = MagicMock()
    logger = MagicMock()

    async def failing_func(self_obj, *args, **kwargs):
        raise ProcessLookupError("denied")

    # Act
    await _collect_and_emit(
        tracker, queue, logger, "Locked OS", failing_func, None, (), {}
    )

    # Assert
    assert queue.empty()
    logger.exception.assert_called_once()
    tracker.get.assert_not_called()


@pytest.mark.asyncio
async def test_collect_and_emit_with_os_error_logs_exception():
    # Arrange
    queue = asyncio.Queue()
    tracker = MagicMock()
    logger = MagicMock()

    async def failing_func(self_obj, *args, **kwargs):
        raise OSError("disk")

    # Act
    await _collect_and_emit(
        tracker, queue, logger, "Network", failing_func, None, (), {}
    )

    # Assert
    logger.exception.assert_called_once()
    assert queue.empty()


# ---------------------------------------------------------------------------
# MetricsService — class behaviour, DIP injection
# ---------------------------------------------------------------------------


def test_metrics_service_init_with_injected_dependencies_sets_attributes(
    metrics_service,
):
    # Arrange - done via fixture

    # Act
    service = metrics_service

    # Assert
    assert service.settings.monitoring.check_interval == 10
    assert service.logger is not None
    assert len(service.valid_methods) == 7


def test_metrics_service_set_event_queue_assigns_queue(metrics_service, event_queue):
    # Arrange
    service = metrics_service

    # Act
    service.set_event_queue(event_queue)

    # Assert
    assert service.event_queue is event_queue


def test_metrics_service_set_state_tracker_assigns_tracker(
    metrics_service, state_manager
):
    # Arrange
    service = metrics_service

    # Act
    service.set_state_tracker(state_manager)

    # Assert
    assert service.state_tracker is state_manager


def test_metrics_service_setup_discovers_decorated_methods(metrics_service):
    # Arrange
    service = metrics_service

    # Act
    discovered = {
        m.__wrapped__.__name__ if hasattr(m, "__wrapped__") else m.__name__
        for m in service.valid_methods
    }

    # Assert
    assert "locked_status" in discovered
    assert "optikey_status" in discovered
    assert "anydesk_status" in discovered
    assert "network_status" in discovered
    assert "charger_status" in discovered
    assert "tobii_hardware_status" in discovered
    assert "check_tobii_status" in discovered


@pytest.mark.asyncio
async def test_metrics_service_start_invokes_all_methods(metrics_service_with_queue):
    # Arrange
    service = metrics_service_with_queue

    # Patch asyncio.gather to avoid infinite loops
    with patch(
        "app.services.metrics.asyncio.gather", new_callable=AsyncMock
    ) as mock_gather:
        mock_gather.return_value = None

        # Act
        await service.start()

        # Assert
        mock_gather.assert_awaited_once()
        # Gather called with 7 coroutines (splat args)
        assert len(mock_gather.call_args.args) == 7

        # Cleanup: close unawaited coroutines to silence RuntimeWarning
        for coro in mock_gather.call_args.args:
            coro.close()


# ---------------------------------------------------------------------------
# MetricsService — individual metric methods (mock to_thread boundary)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locked_status_with_logonui_present_returns_locked_event(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = {"LogonUI.exe", "explorer.exe"}

        # Act
        event = await service.locked_status.__wrapped__(service)

        # Assert
        assert event.status is False
        assert "BLOQUEADA" in event.message
        mock_to_thread.assert_awaited_once()


@pytest.mark.asyncio
async def test_locked_status_without_logonui_returns_unlocked_event(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = {"explorer.exe"}

        # Act
        event = await service.locked_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert "desbloqueada" in event.message


@pytest.mark.asyncio
async def test_optikey_status_with_process_present_returns_open(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = {"OptiKey.exe"}

        # Act
        event = await service.optikey_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert "Aberto" in event.message


@pytest.mark.asyncio
async def test_optikey_status_with_missing_process_returns_closed(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = set()

        # Act
        event = await service.optikey_status.__wrapped__(service)

        # Assert
        assert event.status is False
        assert "Fechado" in event.message


@pytest.mark.asyncio
async def test_anydesk_status_with_process_present_returns_open(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = {"AnyDesk.exe"}

        # Act
        event = await service.anydesk_status.__wrapped__(service)

        # Assert
        assert event.status is True


@pytest.mark.asyncio
async def test_network_status_with_ethernet_up_returns_connected(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    eth = MagicMock(isup=True)
    wifi = MagicMock(isup=False)

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = (eth, wifi)

        # Act
        event = await service.network_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert "Conectado" in event.message


@pytest.mark.asyncio
async def test_network_status_with_all_down_returns_disconnected(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    eth = MagicMock(isup=False)
    wifi = MagicMock(isup=False)

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = (eth, wifi)

        # Act
        event = await service.network_status.__wrapped__(service)

        # Assert
        assert event.status is False
        assert "NÃO CONECTADO" in event.message


@pytest.mark.asyncio
async def test_charger_status_with_no_battery_returns_none_status(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = None

        # Act
        event = await service.charger_status.__wrapped__(service)

        # Assert
        assert event.status is None
        assert event.value is None
        assert "not available" in event.message


@pytest.mark.asyncio
async def test_charger_status_with_plugged_battery_returns_true(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    battery = MagicMock(power_plugged=True, percent=85)

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = battery

        # Act
        event = await service.charger_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert event.value == 85
        assert "Conectada" in event.message


@pytest.mark.asyncio
async def test_charger_status_with_unplugged_battery_returns_false(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    battery = MagicMock(power_plugged=False, percent=42)

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = battery

        # Act
        event = await service.charger_status.__wrapped__(service)

        # Assert
        assert event.status is False


@pytest.mark.asyncio
async def test_tobii_hardware_status_with_tobii_device_returns_connected(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    device = MagicMock()
    device.Name = "Tobii Eye Tracker 5"

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = [device]

        # Act
        event = await service.tobii_hardware_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert "conectado" in event.message


@pytest.mark.asyncio
async def test_tobii_hardware_status_with_no_tobii_returns_disconnected(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    device = MagicMock()
    device.Name = "USB Input Device"

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.return_value = [device]

        # Act
        event = await service.tobii_hardware_status.__wrapped__(service)

        # Assert
        assert event.status is False


@pytest.mark.asyncio
async def test_check_tobii_status_with_all_up_returns_ok(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue
    # First to_thread call returns process names, subsequent calls are service checks
    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        # Call sequence: _collect_process_names, then 3x _is_service_running
        mock_to_thread.side_effect = [
            {
                "Tobii.EyeX.Engine.exe",
                "Tobii.EyeX.Interaction.exe",
                "Tobii.Service.exe",
            },
            True,
            True,
            True,
        ]

        # Act
        event = await service.check_tobii_status.__wrapped__(service)

        # Assert
        assert event.status is True
        assert "UP" in event.message
        assert mock_to_thread.await_count == 4


@pytest.mark.asyncio
async def test_check_tobii_status_with_missing_exe_returns_not_ok(
    metrics_service_with_queue,
):
    # Arrange
    service = metrics_service_with_queue

    with patch(
        "app.services.metrics.asyncio.to_thread", new_callable=AsyncMock
    ) as mock_to_thread:
        mock_to_thread.side_effect = [
            set(),  # no tobii exes
            False,
            False,
            False,
        ]

        # Act
        event = await service.check_tobii_status.__wrapped__(service)

        # Assert
        assert event.status is False
        assert "DOWN" in event.message


# ---------------------------------------------------------------------------
# monitor_metric decorator — interval handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_monitor_metric_with_custom_interval_uses_custom_sleep(
    app_settings, mock_logger
):
    # Arrange
    queue: asyncio.Queue[Event] = asyncio.Queue()
    tracker = MagicMock()
    tracker.get.return_value = Event(message="", status=None)
    service = MetricsService(settings=app_settings, logger=mock_logger)
    service.set_event_queue(queue)
    service.set_state_tracker(tracker)

    call_count = 0

    @__import__("app.services.metrics", fromlist=["monitor_metric"]).monitor_metric(
        resource_name="Test", interval=60
    )
    async def dummy_metric(self) -> Event:
        nonlocal call_count
        call_count += 1
        return Event(message="ok", status=True)

    # Bind as method
    import types

    service.dummy_metric = types.MethodType(dummy_metric, service)

    with patch(
        "app.services.metrics.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError]

        # Act
        try:
            await service.dummy_metric()
        except asyncio.CancelledError:
            pass

        # Assert
        assert call_count >= 1
        first_sleep = mock_sleep.call_args_list[0].args[0]
        assert first_sleep == 60.0


@pytest.mark.asyncio
async def test_monitor_metric_with_no_interval_uses_fallback_check_interval(
    app_settings, mock_logger
):
    # Arrange
    app_settings.monitoring.check_interval = 10
    queue: asyncio.Queue[Event] = asyncio.Queue()
    tracker = MagicMock()
    tracker.get.return_value = Event(message="", status=None)
    service = MetricsService(settings=app_settings, logger=mock_logger)
    service.set_event_queue(queue)
    service.set_state_tracker(tracker)

    @__import__("app.services.metrics", fromlist=["monitor_metric"]).monitor_metric(
        resource_name="Fallback"
    )
    async def dummy_metric(self) -> Event:
        return Event(message="ok", status=True)

    import types

    service.dummy_metric = types.MethodType(dummy_metric, service)

    with patch(
        "app.services.metrics.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError]

        # Act
        try:
            await service.dummy_metric()
        except asyncio.CancelledError:
            pass

        # Assert
        assert mock_sleep.call_args_list[0].args[0] == 10.0
