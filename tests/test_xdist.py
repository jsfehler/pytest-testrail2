import pytest


@pytest.fixture()
def dummy_test_file2(pytester):
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
            c = request.config.pluginmanager
            x = c.getplugin('pytest-testrail-instance')

            assert 1985 == x.testrun_id

        @pytest.mark.case_id('C8765')
        @pytest.mark.defect_ids('PF-418', 'PF-517')
        def test_func_2(request):
            c = request.config.pluginmanager
            x = c.getplugin('pytest-testrail-instance')

            assert 1985 == x.testrun_id

        @pytest.mark.case_id('C1951')
        def test_func_3(request):
            c = request.config.pluginmanager
            x = c.getplugin('pytest-testrail-instance')

            assert 1985 == x.testrun_id

        @pytest.mark.case_id('C2020')
        @pytest.mark.defect_ids('PF-418', 'PF-517')
        def test_func_4(request):
            c = request.config.pluginmanager
            x = c.getplugin('pytest-testrail-instance')

            assert 1985 == x.testrun_id

    """
    pytester.makepyfile(file_data)
    return file_data


def test_xdist_create_new_run(pytester, dummy_test_file2, caplog):
    """Scenario: pytest-xdist is installed

    When pytest is invoked with xdist
    And a testrun_id has not been specified
    Then one new testrun_id is generated
    And the new testrun_id is shared by all xdist workers.
    """
    result = pytester.runpytest("--testrail", "--tr-close-on-complete", "-n 2", '-vvvv')

    result.assert_outcomes(passed=4, skipped=0, failed=0, errors=0)
