import os
import random
import uuid
from typing import Callable, Optional
from unittest.mock import Mock

import pytest

from pytest_testrail.controller import _TestRailController
from pytest_testrail.plugin import PyTestRailPlugin
from pytest_testrail.result_item import ResultItem
from pytest_testrail.store import Store

from .mock_response import MockResponse

pytest_plugins = "pytester"


@pytest.fixture()
def api_client():
    """Get a mock for the TestRailAPI client."""
    client = Mock()

    client.get_run().get.return_value = MockResponse({'is_completed': False})
    client.get_plan().get.return_value = MockResponse({'is_completed': False})
    return client


@pytest.fixture
def tr_controller(api_client):
    return _TestRailController(
        api_client,
        version='1.0.0.0',
        custom_comment="This is custom comment",
        testrun_name=None,
    )


@pytest.fixture
def tr_plugin(api_client, request):
    assign_user_id = 3
    milestone_id = 5
    project_id = 4
    suite_id = 1

    testrail_controller = _TestRailController(
        api_client,
        version='1.0.0.0',
        custom_comment="This is custom comment",
        testrun_name=None,
    )

    return PyTestRailPlugin(
        request.config,
        testrail_controller,
        api_client,
        assign_user_id=assign_user_id,
        project_id=project_id,
        suite_id=suite_id,
        cert_check=False,
        tr_name=None,
        tr_description='This is a test description',
        version='1.0.0.0',
        milestone_id=milestone_id,
    )


@pytest.fixture()
def new_resultitem() -> Callable:
    def _get_result(
        test_name=None,
        case_id=None,
        status_id=None,
        defects=None,
        timestamp=None,
        duration=None,
        comment=None,
        test_parametrize=None,
    ) -> ResultItem:
        test_name = test_name or f'test_foo_{uuid.uuid4()}'
        case_id = case_id or random.randint(1, 1000)
        status_id = status_id
        comment = comment or ''
        timestamp = timestamp or random.random()

        rv = ResultItem(
            test_name=test_name,
            case_id=case_id,
            status_id=status_id,
            duration=duration,
            comment=comment,
            defects=defects,
            test_parametrize=test_parametrize,
            timestamp=timestamp,
        )

        return rv

    return _get_result


@pytest.fixture()
def dummy_test_file(pytester):
    # Register marks
    conftest_source = """
    def pytest_configure(config) -> None:
        # Register marks
        config.addinivalue_line(
            "markers", "case_id(str): Mark tests with a testrail case_id"
        )
        config.addinivalue_line(
            "markers",
            (
                "defect_ids(*str): Mark tests with an issue tracker's IDs."
                "Sent to testrail testrun results."
            )
        )
    """
    pytester.makeconftest(conftest_source)

    file_data = """
        import pytest


        @pytest.mark.case_id('C1234')
        def test_func():
            pass

        @pytest.mark.case_id('C8765')
        @pytest.mark.defect_ids('PF-418', 'PF-517')
        def test_other_func():
            pass
    """
    pytester.makepyfile(file_data)
    return file_data


@pytest.fixture()
def test_items(pytester, dummy_test_file):
    return [item for item in pytester.getitems(dummy_test_file) if item.name != 'testrail']


def pytest_sessionfinish(session, exitstatus):
    """Remove the store file after the tests are finished.

    The tests will invoke the plugin class and create a store file.
    However, the tests do not actually install the plugin.
    As a result, the store file is not cleared when the test session ends.

    This function is a hack to manually remove the store file.
    """
    xdist_worker = os.getenv('PYTEST_XDIST_WORKER')
    xdist_worker_count: Optional[str] = os.getenv('PYTEST_XDIST_WORKER_COUNT')

    if not xdist_worker and not xdist_worker_count:
        Store(session.config).clear()
