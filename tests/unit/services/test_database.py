import pytest

from app.models import Event
from app.services.database import DataBaseConnector, StateManager


def test_state_manager_init_with_no_args_creates_empty_state():
    # Arrange
    # No prior state needed — instantiate directly to test constructor.

    # Act
    manager = StateManager()

    # Assert
    assert manager.get_all() == {}
    assert manager.state == {}


def test_update_state_with_new_key_stores_event(state_manager: StateManager):
    # Arrange
    event = Event(message="hello", status=True)

    # Act
    state_manager.update_state("Optikey", event)

    # Assert
    assert state_manager.get("Optikey") is event


def test_get_with_missing_key_returns_sentinel(state_manager: StateManager):
    # Arrange
    # Fresh manager has no entries.

    # Act
    result = state_manager.get("MissingKey")

    # Assert
    assert result.message == ""
    assert result.status is None
    assert result.event_id is None


def test_get_with_existing_key_returns_stored_event(state_manager: StateManager):
    # Arrange
    event = Event(message="stored", status=False)
    state_manager.update_state("Network", event)

    # Act
    result = state_manager.get("Network")

    # Assert
    assert result is event
    assert result.status is False


def test_get_all_with_multiple_entries_returns_copy(state_manager: StateManager):
    # Arrange
    e1 = Event(message="a", status=True)
    e2 = Event(message="b", status=False)
    state_manager.update_state("A", e1)
    state_manager.update_state("B", e2)

    # Act
    result = state_manager.get_all()

    # Assert
    assert result == {"A": e1, "B": e2}

    # Mutating returned dict must not affect internal state.
    result["C"] = Event(message="c", status=True)

    assert "C" not in state_manager.get_all()


def test_update_state_with_existing_key_overwrites_event(state_manager: StateManager):
    # Arrange
    first = Event(message="first", status=True)
    second = Event(message="second", status=False)
    state_manager.update_state("Key", first)

    # Act
    state_manager.update_state("Key", second)

    # Assert
    assert state_manager.get("Key") is second


def test_update_state_with_multiple_keys_remains_consistent(
    state_manager: StateManager,
):
    # Arrange
    events = [Event(message=f"msg{i}", status=bool(i % 2)) for i in range(10)]

    # Act
    for idx, evt in enumerate(events):
        state_manager.update_state(f"key{idx}", evt)

    # Assert
    all_states = state_manager.get_all()
    assert len(all_states) == 10

    for idx, evt in enumerate(events):
        assert all_states[f"key{idx}"] is evt


def test_database_connector_instantiation_without_implementation_raises_type_error():
    # Arrange
    # DataBaseConnector is abstract — no extra setup needed.

    # Act & Assert
    with pytest.raises(TypeError):
        DataBaseConnector()  # type: ignore[abstract]

    # Assert
    # Exception raised as expected (verified by pytest.raises).


def test_state_manager_is_subclass_of_database_connector_returns_true(
    state_manager: StateManager,
):
    # Arrange
    manager = state_manager

    # Act
    is_subclass = isinstance(manager, DataBaseConnector)

    # Assert
    assert is_subclass is True


def test_get_all_with_empty_state_returns_empty_dict(state_manager: StateManager):
    # Arrange
    # Fresh fixture has no entries.

    # Act
    result = state_manager.get_all()

    # Assert
    assert result == {}
    assert isinstance(result, dict)
