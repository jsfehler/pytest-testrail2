import logging
import os
import time
from typing import Generator, List, Optional, Tuple, cast

from _pytest.config.argparsing import OptionGroup, Parser

import pytest
from pytest import Config

from .config_manager import ConfigManager
from .controller import _TestRailController
from .converters import clean_test_defects, clean_test_ids
from .logger import get_logger
from .result_item import ResultItem
from .results import Results
from .store import Store
from .testrail_api_client import _TestRailAPI


def get_testrail_keys(
    items: List[pytest.Function],
) -> List[Tuple[pytest.Function, List[int]]]:
    """Get Pytest nodes and TestRail ids from pytests markers.

    Returns:
        list[tuple[pytest.Function, list[int]]]:
            Pytest function and the cases associated with them.
    """
    testcaseids = []
    for item in items:
        closest_marker: Optional[pytest.Mark]

        marker = 'case_id'
        closest_marker = item.get_closest_marker(marker)
        if closest_marker:
            raw_ids = cast(Tuple[str], closest_marker.args)
            cleaned_ids = clean_test_ids(raw_ids)
            testcaseids.append((item, cleaned_ids))

    return testcaseids


class PyTestRailPlugin:
    """Plugin class."""

    def __init__(
        self,
        config: Config,
        controller: _TestRailController,
        client: _TestRailAPI,
        assign_user_id: int,
        project_id: int,
        suite_id: int,
        cert_check: bool,
        tr_name: Optional[str] = None,
        tr_description: str = '',
        run_id: int = 0,
        plan_id: int = 0,
        version: str = '',
        close_on_complete: bool = False,
        skip_missing: bool = False,
        milestone_id: Optional[int] = None,
    ):
        self.controller = controller
        self.client = client
        self.assign_user_id = assign_user_id
        self.project_id = project_id
        self.suite_id = suite_id
        self.cert_check = cert_check
        self.testrun_description = tr_description
        self.testrun_id = run_id
        self.testplan_id = plan_id
        self.close_on_complete = close_on_complete

        self.skip_missing = skip_missing
        self.milestone_id = milestone_id

        self.results = Results()

        handler = logging.StreamHandler()
        self.client.logger.addHandler(handler)
        self.client.logger.setLevel(logging.INFO)

        self.logger = get_logger()

        self.case_id_mark = 'case_id'
        self.defect_ids_mark = 'defect_ids'

        self.client.request_kwargs = {
            'verify': self.cert_check,
        }

        self.store = Store(config)
        current_store = self.store.get_all()

        if self.testrun_id and not current_store.get('run_id'):
            self.store.set_value('run_id', self.testrun_id)

        if self.testplan_id and not current_store.get('plan_id'):
            self.store.set_value('plan_id', self.testplan_id)

    def report_header(self) -> str:
        """Get text for pytest's report header."""
        base = 'pytest-testrail:'
        message = 'A new testrun will be created'

        if self.testplan_id:
            message = f'Using existing testplan ID={self.testplan_id}'
        elif self.testrun_id:
            message = f'Using existing testrun ID={self.testrun_id}'

        return f"{base} {message}"

    def pytest_report_header(self, config, startdir) -> str:
        """Add plugin info to header."""
        return self.report_header()

    def set_current_testrun_id(self, config: Config, tr_keys: List[int]) -> None:
        """Get the current testrun's ID or create a new testrun to get an ID."""
        # Guard against creating multiple testruns when using xdist
        run_id: int

        with self.store.lock:
            current_store = self.store.get_all()
            if current_store:
                run_id = current_store['run_id']

            else:
                run_id = self.controller.create_run(
                    assign_user_id=self.assign_user_id,
                    project_id=self.project_id,
                    suite_id=self.suite_id,
                    tr_keys=tr_keys,
                    milestone_id=self.milestone_id,
                    description=self.testrun_description,
                )

                self.store.set_value('run_id', run_id)

        self.testrun_id = run_id
        self.controller.testrun_id = run_id

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items) -> None:
        """Create testrail test run."""
        items_with_tr_keys = get_testrail_keys(items)
        tr_keys = [case_id for item in items_with_tr_keys for case_id in item[1]]

        if self.testrun_id:
            self.testplan_id = 0

            if self.skip_missing:
                tests_response: dict = self.client.get_tests(
                    run_id=self.testrun_id,
                ).get().json()

                self.client.validate_response(tests_response)

                tests: Optional[dict] = tests_response['tests']

                tests_list = []

                if tests:
                    tests_list = [
                        test.get('case_id') for test in tests
                    ]

                for item, case_id in items_with_tr_keys:
                    if not set(case_id).intersection(set(tests_list)):
                        mark = pytest.mark.skip('Test is not present in testrun.')
                        item.add_marker(mark)

        # No testplan_id, no testrun_id
        else:
            self.set_current_testrun_id(config, tr_keys)

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(
        self,
        item: pytest.Item,
        call: pytest.CallInfo,
    ) -> Generator:
        """Collect result and associated TestRail cases of an execution."""
        outcome = yield
        rep = outcome.get_result()
        defectids = None

        if 'callspec' in dir(item):
            test_parametrize = item.callspec.params
        else:
            test_parametrize = None

        comment = rep.longrepr

        defect_ids_marker = item.get_closest_marker(self.defect_ids_mark)
        if defect_ids_marker:
            defectids = defect_ids_marker.args

        case_id_marker = item.get_closest_marker(self.case_id_mark)
        if case_id_marker:
            testcaseids = case_id_marker.args

            if rep.when == 'call' and testcaseids:
                defects = None

                if defectids:
                    defects = str(clean_test_defects(defectids))
                    defects = defects.replace('[', '').replace(']', '').replace("'", '')

                for test_id in clean_test_ids(testcaseids):
                    data = ResultItem(
                        test_name=item.name,
                        case_id=test_id,
                        status_id=outcome.get_result().outcome,
                        duration=rep.duration,
                        comment=comment,
                        defects=defects,
                        test_parametrize=test_parametrize,
                        timestamp=time.time(),
                    )

                    self.results.append(data)

    def pytest_sessionfinish(self, session, exitstatus) -> None:
        """Publish results in TestRail."""
        xdist_worker = os.getenv('PYTEST_XDIST_WORKER')
        xdist_worker_count: Optional[str] = os.getenv('PYTEST_XDIST_WORKER_COUNT')

        if self.results:
            self.controller.upload_results_to_testrail(self.results)

        # pytest-xdist not installed or master session finished
        if not xdist_worker and not xdist_worker_count:
            if self.close_on_complete:
                # Don't rely on the class, always fetch from the store.
                current_store = self.store.get_all()
                self.controller.close_testrail(
                    run_id=current_store.get('run_id'),
                    plan_id=current_store.get('plan_id'),
                )

            # Remove store files when tests are complete.
            self.store.clear()


def pytest_addoption(parser: Parser) -> None:
    """Add plugin options."""
    group: OptionGroup = parser.getgroup('testrail')

    def add(
        option_name: str,
        help_msg: str = '',
        default=None,
        opt_type=None,
        ini_type: str = '',
        **kwargs,
    ) -> None:
        """Add command-line and ini handler for an option.

        ini names are based on the option_name value, with '--' removed and
        dashes replaced with underscores.
        """
        # Handle different store types for options
        if opt_type:
            kwargs['type'] = opt_type

        ini_name: str = option_name.split('--')[1].replace('-', '_')

        group.addoption(
            option_name,
            default=default,
            help=help_msg,
            **kwargs,
        )
        parser.addini(
            ini_name,
            type=ini_type,
            default=default,
            help=help_msg,
        )

    group.addoption(
        '--testrail',
        action='store_true',
        help='Activate the TestRail plugin.',
    )

    add(
        '--tr-url',
        help_msg='Web address used to access a TestRail instance.',
        opt_type=str,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-email',
        help_msg='E-mail address for an account on the TestRail instance.',
        opt_type=str,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-password',
        help_msg='Password for an account on the TestRail instance.',
        opt_type=str,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-timeout',
        help_msg='Timeout for connecting to a TestRail server.',
        opt_type=int,
        ini_type='string',
        action='store',
        default=30,
    )

    add(
        '--tr-testrun-assignedto-id',
        help_msg='ID of the user assigned to the testrun.',
        opt_type=int,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-testrun-project-id',
        help_msg='ID of the project the testrun is in.',
        opt_type=int,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-testrun-suite-id',
        help_msg='ID of the suite containing the testcases.',
        opt_type=int,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-testrun-suite-include-all',
        help_msg='Include all test cases in the specified test suite when creating a new testrun.',
        ini_type='string',
        action='store_true',
    )

    add(
        '--tr-testrun-name',
        help_msg='Name used when creating a new testrun in TestRail.',
        opt_type=str,
        ini_type='string',
        action='store',
    )

    add(
        '--tr-testrun-description',
        help_msg='Description used when creating a new testrun in TestRail.',
        opt_type=str,
        ini_type='string',
        action='store',
        default=None,
    )

    add(
        '--tr-run-id',
        help_msg=(
            'ID of an existing testrun in TestRail.'
            'If given, "--tr-testrun-name" will be ignored.'
        ),
        opt_type=str,
        ini_type='string',
        action='store',
        required=False,
        default=0,
    )

    add(
        '--tr-plan-id',
        help_msg=(
            'ID of an existing testplan to use.'
            'If given, "--tr-testrun-name" will be ignored.'
        ),
        opt_type=str,
        ini_type='bool',
        action='store',
        required=False,
    )

    add(
        '--tr-milestone-id',
        help_msg='ID of milestone used in testrun creation.',
        opt_type=int,
        ini_type='string',
        action='store',
        default=None,
        required=False,
    )

    add(
        '--tr-version',
        help_msg='Specify a version in testcase results.',
        opt_type=str,
        ini_type='string',
        action='store',
        default='',
        required=False,
    )

    add(
        '--tr-no-ssl-cert-check',
        help_msg='Do not check for valid SSL certificate on TestRail host.',
        ini_type='bool',
        action='store_false',
        default=None,
    )

    add(
        '--tr-close-on-complete',
        help_msg='On pytest completion, close the testrun.',
        ini_type='bool',
        action='store_true',
        default=None,
        required=False,
    )

    add(
        '--tr-dont-publish-blocked',
        help_msg='Do not publish results of "blocked" testcases (in TestRail).',
        ini_type='bool',
        action='store_false',
        required=False,
    )

    add(
        '--tr-skip-missing',
        help_msg=(
            'Skip pytest test functions with marks that are not present in a specified testrun.'
        ),
        ini_type='bool',
        action='store_true',
        required=False,
    )

    add(
        '--tr-custom-comment',
        help_msg='Custom text appended to comment for all testcase results.',
        opt_type=str,
        ini_type='string',
        action='store',
        default=None,
        required=False,
    )


def pytest_configure(config: Config) -> None:  # noqa D103
    # Register marks
    config.addinivalue_line(
        "markers", "case_id(str): Mark tests with a testrail case_id",
    )
    config.addinivalue_line(
        "markers",
        (
            "defect_ids(*str): Mark tests with an issue tracker's IDs."
            "Sent to testrail testrun results."
        ),
    )

    use_testrail: bool = config.getoption('--testrail')
    if use_testrail:
        config_manager = ConfigManager(config)

        timeout = int(cast(int, config_manager.get('--tr-timeout', 'tr_timeout')))

        client = _TestRailAPI(
            base_url=cast(str, config_manager.get('--tr-url', 'tr_url')),
            auth=(
                cast(str, config_manager.get('--tr-email', 'tr_email')),
                cast(str, config_manager.get('--tr-password', 'tr_password')),
            ),
            timeout=timeout,
        )

        assign_user_id = config_manager.get(
            '--tr-testrun-assignedto-id',
            'tr_testrun_assignedto_id',
        )
        assign_user_id = cast(int, assign_user_id)

        project_id = config_manager.get(
            '--tr-testrun-project-id',
            'tr_testrun_project_id',
        )
        project_id = cast(int, project_id)

        suite_id = config_manager.get(
            '--tr-testrun-suite-id',
            'tr_testrun_suite_id',
        )
        suite_id = cast(int, suite_id)

        include_all = config_manager.get(
            '--tr-testrun-suite-include-all',
            'tr_testrun_suite_include_all',
        )
        include_all = cast(bool, include_all)

        cert_check = config_manager.get(
            '--tr-no-ssl-cert-check',
            'tr_no_ssl_cert_check',
        )
        cert_check = cast(bool, cert_check)

        tr_name = config_manager.get(
            '--tr-testrun-name',
            'tr_testrun_name',
        )
        tr_name = cast(str, tr_name)

        tr_description = config_manager.get(
            '--tr-testrun-description',
            'tr_testrun_description',
        )
        tr_description = cast(str, tr_description)

        run_id = config_manager.get('--tr-run-id')
        run_id = cast(int, run_id)

        plan_id = config_manager.get(
            '--tr-plan-id',
            'tr_plan_id',
        )
        plan_id = cast(int, plan_id)

        version = config_manager.get('--tr-version')
        version = cast(str, version)

        close_on_complete = config_manager.get('--tr-close-on-complete')
        close_on_complete = cast(bool, close_on_complete)

        custom_comment = config_manager.get(
            '--tr-custom-comment',
            'tr_custom_comment',
        )
        custom_comment = cast(str, custom_comment)

        milestone_id = config_manager.get(
            '--tr-milestone-id',
            'tr_milestone_id',
        )
        milestone_id = cast(int, milestone_id)

        publish_blocked = config_manager.get('--tr-dont-publish-blocked')
        publish_blocked = cast(bool, publish_blocked)

        skip_missing = config_manager.get('--tr-skip-missing')
        skip_missing = cast(bool, skip_missing)

        testrail_controller = _TestRailController(
            client,
            publish_blocked=publish_blocked,
            include_all=include_all,
            version=version,
            custom_comment=custom_comment,
            testrun_name=tr_name,
            testrun_id=run_id,
            testplan_id=plan_id,
        )

        config.pluginmanager.register(
            PyTestRailPlugin(
                config=config,
                controller=testrail_controller,
                client=client,
                assign_user_id=assign_user_id,
                project_id=project_id,
                suite_id=suite_id,
                cert_check=cert_check,
                tr_name=tr_name,
                tr_description=tr_description,
                run_id=run_id,
                plan_id=plan_id,
                version=version,
                close_on_complete=close_on_complete,
                skip_missing=skip_missing,
                milestone_id=milestone_id,
            ),
            # Name of plugin instance (allow to be used by other plugins)
            name="pytest-testrail-instance",
        )
