from unittest import mock

import pytest

from pytest_testrail.controller import _TestRailController

from .mock_response import MockResponse, get_plan_response


def test_new_testrun_name_format(api_client):
    """New testruns have a date suffix in the format: '%d-%m-%Y %H:%M:%S'"""
    manager = _TestRailController(api_client)

    new_name_pieces = manager._new_testrun_name().split(' ')

    assert new_name_pieces[0] == 'Automated'
    assert new_name_pieces[1] == 'Run'
    assert len(new_name_pieces[2].split('-')) == 3
    assert len(new_name_pieces[3].split(':')) == 3


def test_get_available_testruns(api_client):
    """Test of method `get_available_testruns`"""
    testplan_id = 100

    manager = _TestRailController(api_client)

    manager.client.get_plan().get.return_value = get_plan_response
    assert manager.get_open_runs(testplan_id) == [59, 61]


def test_create_run(api_client):
    mock_client = mock.Mock()
    mock_client.add_run().post().json.return_value = {'id': 100}

    manager = _TestRailController(mock_client)

    result = manager.create_run(
        0, 0, 0, False, [1, 2, 3],
    )

    assert result == 100


def test_controller_testplan_completed(api_client):
    mock_client = mock.Mock()
    mock_client.get_plan().get.return_value = MockResponse({"is_completed": True})

    with pytest.raises(Exception) as exc:
        _TestRailController(mock_client, testplan_id=248)

    assert str(exc.value) == "Test plan is marked as completed."


def test_controller_testrun_completed(api_client):
    mock_client = mock.Mock()
    mock_client.get_run().get.return_value = MockResponse({"is_completed": True})

    with pytest.raises(Exception) as exc:
        _TestRailController(mock_client, testrun_id=248)

    assert str(exc.value) == "Test run is marked as completed."
