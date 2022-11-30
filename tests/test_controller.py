from unittest import mock

import pytest

from pytest_testrail.controller import _TestRailController
from pytest_testrail.results import Results

from .mock_response import MockResponse, get_plan_response


def test_new_testrun_name_format(api_client):
    """New testruns have a date suffix in the format: '%d-%m-%Y %H:%M:%S'"""
    controller = _TestRailController(api_client)

    new_name_pieces = controller._new_testrun_name().split(' ')

    assert new_name_pieces[0] == 'Automated'
    assert new_name_pieces[1] == 'Run'
    assert len(new_name_pieces[2].split('-')) == 3
    assert len(new_name_pieces[3].split(':')) == 3


def test_get_available_testruns(api_client):
    """Test of method `get_available_testruns`"""
    testplan_id = 100

    controller = _TestRailController(api_client)

    controller.client.get_plan().get.return_value = get_plan_response
    assert controller.get_open_runs(testplan_id) == [59, 61]


def test_create_run(api_client):
    mock_client = mock.Mock()
    mock_client.add_run().post().json.return_value = {'id': 100}

    controller = _TestRailController(mock_client)

    result = controller.create_run(
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


def test_controller_close_testrail_run_id():
    mock_client = mock.Mock()
    mock_client.close_run().get.return_value = MockResponse({"is_completed": True})

    controller = _TestRailController(mock_client)

    controller.close_testrail(run_id=10)

    controller.client.close_run().post.assert_called()


def test_controller_close_testrail_plan_id():
    mock_client = mock.Mock()
    mock_client.close_plan().get.return_value = MockResponse({"is_completed": True})

    controller = _TestRailController(mock_client)

    controller.close_testrail(plan_id=10)

    controller.client.close_plan().post.assert_called()


def test_controller_upload_results_to_testrail_has_testplan_id(
    new_resultitem, mocker,
):
    mock_get_open_runs = mocker.patch(
        'pytest_testrail.controller._TestRailController.get_open_runs',
    )
    mock_get_open_runs.return_value = [1, 2]

    mocker.patch('pytest_testrail.controller._TestRailController.send_to_testrail')

    mock_client = mocker.Mock()
    mock_client.close_plan().get.return_value = MockResponse({"is_completed": True})

    controller = _TestRailController(mock_client)
    controller.testplan_id = 3124

    resultitems = [
        new_resultitem(
            test_name='test_foo',
            case_id=5678,
            status_id="skipped",
            duration=0.1,
            timestamp=999,
            comment="An error",
        ),
        new_resultitem(
            test_name='test_foo',
            case_id=1234,
            status_id="passed",
            duration=2.6,
            timestamp=999,
        ),
    ]

    results = Results()
    for result in resultitems:
        results.append(result)

    controller.upload_results_to_testrail(results)

    controller.get_open_runs.assert_called()
    controller.send_to_testrail.assert_called()
