from datetime import datetime
from typing import Optional

from .logger import get_logger
from .results import Results
from .status import TESTRAIL_TEST_STATUS
from .testrail_api_client import _TestRailAPI


class _TestRailController:
    def __init__(
        self,
        client: _TestRailAPI,
        publish_blocked: bool = False,
        include_all: bool = False,
        version: str = '',
        custom_comment: Optional[str] = '',
        testrun_name: Optional[str] = '',
        testrun_id: int = 0,
        testplan_id: int = 0,
    ):
        self.client = client
        self.publish_blocked = publish_blocked
        self.include_all = include_all
        self.version = version
        self.custom_comment = custom_comment
        self.testrun_id = testrun_id
        self.testplan_id = testplan_id

        self.new_testrun_name_date_format = '%d-%m-%Y %H:%M:%S'
        self.testrun_name = testrun_name or self._new_testrun_name()

        self.logger = get_logger()

        self.comment_size_limit = 4000

        # Sanity check against desired configuration against TestRail.
        if self.testplan_id:
            plan_response = self.client.get_plan(plan_id=self.testplan_id).get().json()

            self.client.validate_response(plan_response)

            if plan_response.get('is_completed'):
                raise Exception('Test plan is marked as completed.')

        if self.testrun_id:
            run_response = self.client.get_run(run_id=self.testrun_id).get().json()

            self.client.validate_response(run_response)

            if run_response.get('is_completed'):
                raise Exception('Test run is marked as completed.')

    def _new_testrun_name(self) -> str:
        """Get a new testrun name using a timestamp."""
        now = datetime.utcnow()

        return f'Automated Run {now.strftime(self.new_testrun_name_date_format)}'

    def get_open_runs(self, plan_id: int) -> list:
        """Get a list of available testruns associated to a testplan in TestRail."""
        testruns_list = []

        response = self.client.get_plan(plan_id=plan_id).get().json()

        self.client.validate_response(response)

        for entry in response['entries']:
            for run in entry['runs']:
                if not run['is_completed']:
                    testruns_list.append(run['id'])

        return testruns_list

    def create_run(
        self,
        assign_user_id: int,
        project_id: int,
        suite_id: int,
        tr_keys: list[int],
        milestone_id: Optional[int] = None,
        description: str = '',
    ) -> int:
        """Create test run with ids collected from markers."""
        # prompt enabling include all test cases from test suite when creating test run
        if self.include_all:
            self.logger.info(
                'Option "Include all testcases from test suite for test run" active.',
            )

        data = {
            'suite_id': suite_id,
            'name': self.testrun_name,
            'description': description,
            'assignedto_id': assign_user_id,
            'include_all': self.include_all,
            'case_ids': tr_keys,
            'milestone_id': milestone_id,
        }

        response = self.client.add_run(project_id=project_id).post(
            json=data,
        ).json()

        self.client.validate_response(response)

        testrun_id: int = response['id']
        self.logger.info(
            (
                f'New testrun created with name '
                f'"{self.testrun_name}" and ID={testrun_id}'
            ),
        )

        return testrun_id

    def get_blocked_cases(self, testrun_id: int) -> list[Optional[int]]:
        rv: list[Optional[int]] = []

        response: dict = self.client.get_tests(run_id=testrun_id).get().json()

        self.client.validate_response(response)

        tests: list[dict] = response['tests']

        if tests:
            rv = [
                test.get('case_id') for test in tests
                if test.get('status_id') == TESTRAIL_TEST_STATUS["blocked"]
            ]

        return rv

    def send_to_testrail(self, testrun_id: int, results: Results) -> None:
        """Add results one by one to improve errors handling.

        Results are sorted by case_id, by name, by run order, then by status_id.

        If a case_id has multiple results with the same name (i.e.: Reruns),
        they will be updated in chronological order.

        if a case_id has multiple results with different names (i.e.: Parametrized),
        failing results will be updated last.

        if a case_id has multiple results with same and different names
        (i.e.: Rerun and parametrized),
        failing results relative to the latest run will be updated last.

        Arguments:
            testrun_id: Id of the testrun to feed
        """
        self.results = results._sort()

        # Exclude testcases with "blocked" status.
        if self.publish_blocked is False:
            self.logger.info('Blocked testcases will not be published.')

            blocked_cases = self.get_blocked_cases(testrun_id)

            blocked_test_str = ', '.join(str(c) for c in blocked_cases)
            self.logger.info(
                (
                    "Blocked testcases excluded:"
                    f"{blocked_test_str}."
                ),
            )

            self.results = [
                result for result in self.results if result.case_id not in blocked_cases
            ]

        # Publish results
        post_data: dict[str, list] = {'results': []}

        for result in self.results:
            entry = result.as_api_payload(
                custom_comment=self.custom_comment,
                comment_size_limit=self.comment_size_limit,
            )

            if self.version:
                entry['version'] = self.version

            post_data['results'].append(entry)

        response = self.client.add_results_for_cases(run_id=testrun_id).post(
            json=post_data,
        ).json()

        self.client.validate_response(response)

    def upload_results_to_testrail(self, results: Results) -> None:
        tests_list = ', '.join([str(result.case_id) for result in results])
        self.logger.info(f"Publishing testcases: {tests_list}.")

        if self.testrun_id:
            self.send_to_testrail(self.testrun_id, results)

        elif self.testplan_id:
            testruns = self.get_open_runs(self.testplan_id)

            self.logger.info(
                f"Updating testruns: {', '.join([str(elt) for elt in testruns])}.",
            )
            for testrun_id in testruns:
                self.send_to_testrail(testrun_id, results)

        self.logger.info('Publishing complete.')

    def close_testrail(self) -> None:
        """Close the testrun or testplan used by the tests."""
        if self.testrun_id:
            response = self.client.close_run(run_id=self.testrun_id).post(
                json={},
            ).json()

            self.client.validate_response(response)
            self.logger.info(f'Test run with ID={self.testrun_id} was closed')

        elif self.testplan_id:
            response = self.client.close_plan(plan_id=self.testplan_id).post(
                json={},
            ).json()

            self.client.validate_response(response)
            self.logger.info(f'Test plan with ID={self.testplan_id} was closed')
