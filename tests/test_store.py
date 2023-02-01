import pytest

from pytest_testrail.store import Store


def test_store_set_value_error(request):
    """Scenario: Tried to set a value into the store multiple times.

    When the user tries to set a value for a key that is already in the store
    Then a ValueError is raised
    """
    store = Store(request.config)

    store.set_value('cherry', 11001110)

    with pytest.raises(ValueError):
        store.set_value('cherry', 22002220)


def test_store_no_file(request):
    """Scenario: Tried to clear the store but no store file exists

    When Store().clear() is called
    And no operation has created the store file
    Then nothing happens
    """
    store = Store(request.config)

    store.clear()
