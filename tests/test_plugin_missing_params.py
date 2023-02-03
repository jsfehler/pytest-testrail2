import pytest


@pytest.fixture()
def test_plugin_missing_url_dummy_file(pytester):
    # Register marks
    conftest_source = """
    from unittest.mock import Mock
    import pytest_testrail
    import random

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

        # Instead of calling TestRail for a new run,
        # Use an iterator that should only be called once.
        foo = iter([1985, 1986])

        m = Mock()
        m.return_value = random.randint(1, 1000)
        pytest_testrail.controller._TestRailController.create_run = m
        pytest_testrail.controller._TestRailController.create_run.return_value = next(foo)

        pytest_testrail.plugin._TestRailAPI = Mock()
    """
    pytester.makeconftest(conftest_source)

    file_data = """
        import pytest

        @pytest.mark.case_id('C1234')
        def test_func_1(request):
            assert True

    """
    pytester.makepyfile(file_data)
    return file_data


def test_plugin_missing_url(pytester, test_plugin_missing_url_dummy_file):
    """Scenario: missing TestRail URL

    When pytest is invoked with xdist
    And a testrun_id has not been specified
    Then one new testrun_id is generated
    And the new testrun_id is shared by all xdist workers.
    """
    result = pytester.runpytest(
        '--testrail',
        '--tr-email=dummy',
        '--tr-password=dummy',
    )

    assert result.errlines == ['Exit: A TestRail URL is required.']


def test_plugin_missing_auth(pytester, test_plugin_missing_url_dummy_file):
    """Scenario: missing TestRail credentials

    When pytest is invoked with xdist
    And a testrun_id has not been specified
    Then one new testrun_id is generated
    And the new testrun_id is shared by all xdist workers.
    """
    result = pytester.runpytest(
        '--testrail',
        '--tr-url=dummy',
    )

    assert result.errlines == ['Exit: TestRail credentials are required.']
