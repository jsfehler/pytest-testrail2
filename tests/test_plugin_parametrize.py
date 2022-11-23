from unittest import mock

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


        @pytest.mark.parametrize(
            "my_var",
            [
                pytest.param(10, marks=pytest.mark.case_id('C1951')),
                pytest.param(11, marks=pytest.mark.case_id('C1952')),
                pytest.param(12, marks=pytest.mark.case_id('C1953')),
            ],
        )
        def test_func_1(request, my_var):
            assert True
    """
    pytester.makepyfile(file_data)
    return file_data


def test_pytest_runtest_makereport_parametrize(
    tr_plugin, pytester, new_resultitem, dummy_test_file2,
):
    test_items = [item for item in pytester.getitems(dummy_test_file2) if item.name != 'testrail']

    # --------------------------------
    # This part of code is a little tricky: it fakes the execution of
    # pytest_runtest_makereport
    # by artificially send a stub object (Outcome)
    class Outcome:
        def __init__(self):
            self.result = pytester.runpytest()
            setattr(self.result, "when", "call")
            setattr(self.result, "longrepr", "An error")
            setattr(self.result, "outcome", "failed")
            self.result.duration = 2

        def get_result(self):
            return self.result

    outcome = Outcome()

    # Mock the timestamp
    with mock.patch("time.time") as mock_time:
        mock_time.return_value = 999

        f = tr_plugin.pytest_runtest_makereport(test_items[0], None)
        f.send(None)
        try:
            f.send(outcome)
        except StopIteration:
            pass
    # --------------------------------

    assert len(tr_plugin.results) == 1
    assert tr_plugin.results[0].test_parametrize == {'my_var': 10}
