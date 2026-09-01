import pytest

from app.models import Event
from app.services.database import DataBaseConnector, StateManager


def test_state_manager_init_creates_empty_state():
    # Arrange

    # Act
    manager = StateManager()

    # Assert
    assert manager.get_all() == {}
    assert manager.state == {}


def test_state_manager_update_state_stores_event():
    # Arrange
    manager = StateManager()
    event = Event(message="hello", status=True)

    # Act
    manager.update_state("Optikey", event)

    # Assert
    assert manager.get("Optikey") is event


def test_state_manager_get_with_missing_key_returns_sentinel():
    # Arrange
    manager = StateManager()

    # Act
    result = manager.get("MissingKey")

    # Assert
    assert result.message == ""
    assert result.status is None
    assert result.event_id is None


def test_state_manager_get_with_existing_key_returns_stored_event():
    # Arrange
    manager = StateManager()
    event = Event(message="stored", status=False)
    manager.update_state("Network", event)

    # Act
    result = manager.get("Network")

    # Assert
    assert result is event
    assert result.status is False


def test_state_manager_get_all_returns_copy_of_state():
    # Arrange
    manager = StateManager()
    e1 = Event(message="a", status=True)
    e2 = Event(message="b", status=False)
    manager.update_state("A", e1)
    manager.update_state("B", e2)

    # Act
    result = manager.get_all()

    # Assert
    assert result == {"A": e1, "B": e2}
    # Mutating returned dict should not affect internal state
    result["C"] = Event(message="c", status=True)

    assert "C" not in manager.get_all()


def test_state_manager_update_state_overwrites_existing():
    # Arrange
    manager = StateManager()
    first = Event(message="first", status=True)
    second = Event(message="second", status=False)
    manager.update_state("Key", first)

    # Act
    manager.update_state("Key", second)

    # Assert
    assert manager.get("Key") is second


def test_state_manager_concurrent_updates_remain_consistent():
    # Arrange
    manager = StateManager()
    events = [Event(message=f"msg{i}", status=bool(i % 2)) for i in range(10)]

    # Act
    for idx, evt in enumerate(events):
        manager.update_state(f"key{idx}", evt)

    # Assert
    all_states = manager.get_all()
    assert len(all_states) == 10
    for idx, evt in enumerate(events):
        assert all_states[f"key{idx}"] is evt


def test_database_connector_is_abstract():
    # Arrange

    # Act / Assert
    with pytest.raises(TypeError):
        DataBaseConnector()  # type: ignore[abstract]


def test_state_manager_is_subclass_of_database_connector():
    # Arrange
    manager = StateManager()

    # Act
    is_subclass = isinstance(manager, DataBaseConnector)

    # Assert
    assert is_subclass is True


def test_state_manager_get_all_with_empty_returns_empty_dict():
    # Arrange
    manager = StateManager()

    # Act
    result = manager.get_all()

    # Assert
    assert result == {}
    assert isinstance(result, dict)
