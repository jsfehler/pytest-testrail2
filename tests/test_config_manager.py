import pytest


@pytest.fixture()
def mock_config_file(pytester):
    # Create mock config file
    source = """
    [pytest]
    dummy = 200
    dummy_b = True
    """
    pytester.makeini(source)


@pytest.fixture()
def mock_conftest(pytester):
    conftest_source = """
    def pytest_addoption(parser) -> None:
        group: OptionGroup = parser.getgroup('test_mock')

        group.addoption(
            '--tr-dummy',
            action='store',
        )
        parser.addini(
            'dummy',
            help='',
        )

        group.addoption(
            '--tr-dummy-b',
            action='store',
        )
        parser.addini(
            'dummy_b',
            type='bool',
            help='',
        )
    """
    pytester.makeconftest(conftest_source)


def test_config_manager_cli(pytester, mock_config_file, mock_conftest):
    """Scenario:

    Given an instance of ConfigManager
    And the instance is using the pytest config object
    When pytest is invoked with a valid option
    When getoption() is called with the same valid option
    Then the value is retrieved
    """
    test_file_source = """
    from pytest_testrail.config_manager import ConfigManager


    def test_cfg_1(pytestconfig):

        config_manager = ConfigManager(pytestconfig)

        result = config_manager.get("--tr-dummy", "dummy")

        assert result == '400'
    """

    pytester.makefile('.py', test_foo=test_file_source)

    result = pytester.runpytest("--tr-dummy=400")

    result.assert_outcomes(passed=1, skipped=0, failed=0, errors=0)


def test_config_manager_from_file(pytester, mock_config_file, mock_conftest):
    test_file_source = """
    from pytest_testrail.config_manager import ConfigManager


    def test_cfg_1(pytestconfig):

        config_manager = ConfigManager(pytestconfig)

        result = config_manager.get("--tr-dummy", "dummy")

        assert result == '200'
    """

    pytester.makefile('.py', test_foo=test_file_source)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1, skipped=0, failed=0, errors=0)


def test_config_manager_from_file_bool(pytester, mock_config_file, mock_conftest):
    test_file_source = """
    from pytest_testrail.config_manager import ConfigManager


    def test_cfg_2(pytestconfig):

        config_manager = ConfigManager(pytestconfig)

        result = config_manager.get(
            "--tr-dummy-b", "dummy_b",
        )

        assert result == True
    """

    pytester.makefile('.py', test_foo_2=test_file_source)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1, skipped=0, failed=0, errors=0)
