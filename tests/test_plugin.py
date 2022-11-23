from unittest import mock
from unittest.mock import call, patch

from pytest_testrail import plugin
from pytest_testrail.controller import _TestRailController
from pytest_testrail.plugin import (
    PyTestRailPlugin,
)
from pytest_testrail.status import (
    TESTRAIL_TEST_STATUS,
)

from .mock_response import MockResponse, get_plan_response

ASSIGN_USER_ID = 3

PROJECT_ID = 4

SUITE_ID = 1
TR_NAME = None
DESCRIPTION = 'This is a test description'
CUSTOM_COMMENT = "This is custom comment"


class Outcome:
    """Mock a pytest outcome."""

    def __init__(self, pytester):
        self.result = pytester.runpytest()
        setattr(self.result, "when", "call")
        setattr(self.result, "longrepr", "An error")
        setattr(self.result, "outcome", "failed")
        self.result.duration = 2

    def get_result(self):
        return self.result


def test_get_testrail_keys(test_items):
    items = plugin.get_testrail_keys(test_items)
    assert list(items[0][1]) == [1234]
    assert list(items[1][1]) == [8765]


def test_pytest_runtest_makereport(
    test_items, tr_plugin, pytester, new_resultitem, dummy_test_file,
):

    # Fake the execution of pytest_runtest_makereport
    # by artificially send a stub object (Outcome)
    outcome = Outcome(pytester)

    # Mock the timestamp
    with patch("time.time") as mock_time:
        mock_time.return_value = 999

        f = tr_plugin.pytest_runtest_makereport(test_items[0], None)
        f.send(None)
        try:
            f.send(outcome)
        except StopIteration:
            pass

    expected_results = [
        new_resultitem(
            test_name='test_func',
            case_id=1234,
            status_id="failed",
            duration=2,
            comment="An error",
            timestamp=999,
        )
    ]

    assert tr_plugin.results == expected_results


def test_pytest_sessionfinish(api_client, tr_plugin, new_resultitem):
    results = [
        new_resultitem(
            case_id=5678,
            status_id="skipped",
            comment="An error",
            timestamp=1,
            duration=0.1,
        ),
        new_resultitem(
            case_id=1234,
            status_id="failed",
            defects='PF-516',
            timestamp=0.5,
            duration=2.6,
        ),
        new_resultitem(
            case_id=1234,
            status_id="passed",
            defects=['PF-517', 'PF-113'],
            timestamp=2,
            duration=2.6,
        ),
    ]
    for result in results:
        tr_plugin.results.append(result)

    tr_plugin.testrun_id = 10
    tr_plugin.controller.testrun_id = 10

    get_tests_return_value = {
        'tests': [],
    }
    tr_plugin.controller.client.get_tests().get.return_value = MockResponse(get_tests_return_value)

    tr_plugin.pytest_sessionfinish(mock.Mock(), 0)

    expected_data = {
        'results': [
            {
                'case_id': 1234,
                'status_id': TESTRAIL_TEST_STATUS["passed"],
                'defects':['PF-517', 'PF-113'],
                'version': '1.0.0.0',
                'elapsed': '3s',
                'comment': f'# Pytest result: #\n{CUSTOM_COMMENT}\n',
            },
            {
                'case_id': 5678,
                'status_id': TESTRAIL_TEST_STATUS["blocked"],
                'defects': None,
                'version': '1.0.0.0',
                'elapsed': '1s',
                'comment': f'# Pytest result: #\n{CUSTOM_COMMENT}\n    An error\n',
            },
            {
                'case_id': 1234,
                'status_id': TESTRAIL_TEST_STATUS["failed"],
                'defects':'PF-516',
                'version': '1.0.0.0',
                'elapsed': '3s',
                'comment': f'# Pytest result: #\n{CUSTOM_COMMENT}\n',
            },
        ]
    }

    api_client.add_results_for_cases().post.assert_called()

    api_client.add_results_for_cases().post.assert_any_call(
        json=expected_data,
    )


def test_pytest_sessionfinish_testplan(api_client, tr_plugin, new_resultitem):
    results = [
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
    for result in results:
        tr_plugin.results.append(result)

    tr_plugin.testplan_id = 100
    tr_plugin.testrun_id = 0
    tr_plugin.controller.testplan_id = 100
    tr_plugin.controller.testrun_id = 0

    get_tests_return_value = {
        'tests': [],
    }
    tr_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)

    tr_plugin.client.get_plan().get.return_value = get_plan_response

    tr_plugin.pytest_sessionfinish(mock.Mock(), 0)
    expected_data = {
        'results': [
            {
                'case_id': 1234,
                'status_id': TESTRAIL_TEST_STATUS["passed"],
                'version': '1.0.0.0',
                'elapsed': '3s',
                'defects': None,
                'comment': f'# Pytest result: #\n{CUSTOM_COMMENT}\n',
            },
            {
                'case_id': 5678,
                'status_id': TESTRAIL_TEST_STATUS["blocked"],
                'version': '1.0.0.0',
                'elapsed': '1s',
                'defects': None,
                'comment': f'# Pytest result: #\n{CUSTOM_COMMENT}\n    An error\n',
            }
        ]
    }

    api_client.add_results_for_cases().post.assert_called()

    api_client.add_results_for_cases().post.assert_any_call(
        json=expected_data,
    )


def test_close_test_run(api_client, tr_controller, new_resultitem, caplog):
    tr_controller.testrun_id = 10

    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        cert_check=False,
        tr_name=TR_NAME,
        run_id=10,
        version='1.0.0.0',
        close_on_complete=True,
    )

    results = [
        new_resultitem(
            case_id=1234,
            status_id="failed",
        ),
        new_resultitem(
            case_id=5678,
            status_id="skipped",
            comment="An error",
        ),
        new_resultitem(
            case_id=1234,
            status_id="passed",
            comment="An error",
        ),
    ]

    for result in results:
        my_plugin.results.append(result)

    get_tests_return_value = {
        'tests': [],
    }
    my_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)

    my_plugin.pytest_sessionfinish(mock.Mock(), 0)

    assert caplog.records[-1].msg == 'Test run with ID=10 was closed'


def test_close_test_plan(api_client, tr_controller, new_resultitem, caplog):
    tr_controller.testplan_id = 10

    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        cert_check=False,
        tr_name=TR_NAME,
        plan_id=10,
        version='1.0.0.0',
        close_on_complete=True,
    )

    results = [
        new_resultitem(
            case_id=5678,
            status_id="skipped",
            comment="An error",
        ),
        new_resultitem(
            case_id=1234,
            status_id="passed",
        ),
    ]

    for result in results:
        my_plugin.results.append(result)

    get_tests_return_value = {
        'tests': [],
    }
    my_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)

    my_plugin.client.get_plan().get.return_value = get_plan_response
    my_plugin.pytest_sessionfinish(mock.Mock(), 0)

    assert caplog.records[-1].msg == 'Test plan with ID=10 was closed'


def test_publish_blocked_disabled(api_client, new_resultitem):
    """Scenario:

    Given a testcase has 'blocked' status
    And 'publish_blocked' == False
    When testcases are published to TestRail
    Then 'blocked' testcases will not be published.
    """
    tr_controller = _TestRailController(
        api_client,
        publish_blocked=False,
        version='1.0.0.0',
        custom_comment="This is custom comment",
        testrun_name=None,
        testrun_id=10,
    )

    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        assign_user_id=ASSIGN_USER_ID,
        project_id=PROJECT_ID,
        suite_id=SUITE_ID,
        cert_check=True,
        tr_name=TR_NAME,
        version='1.0.0.0',
        run_id=10
    )

    results = [
        new_resultitem(
            case_id=1234,
            status_id="skipped",
            defects=None,
            timestamp=0.1,
        ),
        new_resultitem(
            case_id=5678,
            status_id="passed",
            defects=None,
            timestamp=0.1,
        ),
    ]
    for result in results:
        my_plugin.results.append(result)

    get_tests_return_value = {
        'tests': [
            {
                'case_id': 1234,
                'status_id': TESTRAIL_TEST_STATUS["blocked"],
                'defects': None,
                'timestamp': 0.1,
                'elapsed': '',
            },
            {
                'case_id': 5678,
                'status_id': TESTRAIL_TEST_STATUS["passed"],
                'defects': None,
                'timestamp': 0.1,
                'elapsed': '',
            },
        ]
    }
    my_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)

    my_plugin.pytest_sessionfinish(mock.Mock(), 0)

    my_plugin.client.get_tests().get.assert_called_once_with()

    expected_data = {
        'results': [
            {
                'status_id': TESTRAIL_TEST_STATUS["passed"],
                'case_id': 5678,
                'defects': None,
                'version': '1.0.0.0',
                'elapsed': '',
                'comment': '# Pytest result: #\nThis is custom comment\n',
            }
        ]
    }
    assert len(my_plugin.client.add_results_for_cases().post.call_args_list) == 1

    expected_call = call(json=expected_data)
    assert my_plugin.client.add_results_for_cases().post.call_args_list[0] == expected_call


def test_skip_missing_only_one_test(api_client, tr_controller, test_items):
    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        False,
        True,
        TR_NAME,
        run_id=10,
        version='1.0.0.0',
        skip_missing=True,
    )

    get_tests_return_value = {
        'tests': [
            {
                'case_id': 1234,
            },
            {
                'case_id': 5678,
            },
        ]
    }

    my_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)
    my_plugin.client.get_run().get.return_value = MockResponse({'is_completed': False})

    my_plugin.pytest_collection_modifyitems(None, None, test_items)

    assert not test_items[0].get_closest_marker('skip')
    assert test_items[1].get_closest_marker('skip')


def test_skip_missing_correlation_tests(api_client, tr_controller, test_items):
    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        False,
        True,
        TR_NAME,
        run_id=10,
        version='1.0.0.0',
        skip_missing=True,
    )

    get_tests_return_value = {
        'tests': [
            {
                'case_id': 1234,
            },
            {
                'case_id': 8765,
            },
        ]
    }

    my_plugin.client.get_tests().get.return_value = MockResponse(get_tests_return_value)
    my_plugin.client.get_run().get.return_value = MockResponse({'is_completed': False})

    my_plugin.pytest_collection_modifyitems(None, None, test_items)

    assert not test_items[0].get_closest_marker('skip')
    assert not test_items[1].get_closest_marker('skip')


def test_report_header_run(api_client, tr_controller):
    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        False,
        True,
        TR_NAME,
        run_id=10,
        version='1.0.0.0',
        skip_missing=True,
    )

    result = my_plugin.report_header()

    assert result == 'pytest-testrail: Using existing testrun ID=10'


def test_report_header_plan(api_client, tr_controller):
    my_plugin = PyTestRailPlugin(
        tr_controller,
        api_client,
        ASSIGN_USER_ID,
        PROJECT_ID,
        SUITE_ID,
        False,
        True,
        TR_NAME,
        plan_id=10,
        version='1.0.0.0',
        skip_missing=True,
    )

    result = my_plugin.report_header()

    assert result == 'pytest-testrail: Using existing testplan ID=10'
