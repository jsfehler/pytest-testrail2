from collections import UserList
from itertools import groupby
from operator import attrgetter
from typing import List

from .result_item import ResultItem


class Results(UserList):
    """Store ResultItem objects."""

    def append(self, item: ResultItem) -> None:
        """Mimic default list behaviour."""
        self.data.append(item)

    def _sort(self) -> List[ResultItem]:
        """Sort Pytest results to make sense for TestRail."""
        # Every result, split by test_name
        all_split_by_test_name: List[List[ResultItem]] = []

        # First: Sort and split results by case_id
        results = sorted(self.data, key=attrgetter('case_id'))
        case_ids = groupby(results, lambda x: x.case_id)

        # For each case_id:
        for _case_id, cases_by_id in case_ids:
            _cases_list: List[ResultItem] = list(cases_by_id)

            # Second: Sort and split each case_id group by:
            #     test_name, secondary sort by timestamp
            # Handle rare scenario with same id, different test name
            _cases_list.sort(key=attrgetter('test_name', 'timestamp'))

            # Split by test_name.
            test_name_group = groupby(_cases_list, lambda x: x.test_name)

            # Third: Sort every test_name group by timestamp
            #     This handles reruns.
            #     Newest test is always the last published result
            for _test_name, cases_by_test_name in test_name_group:
                test_name_cases_list = list(cases_by_test_name)
                test_name_cases_list.sort(key=attrgetter('timestamp'))

                all_split_by_test_name.append(test_name_cases_list)

        # Fourth: Sort list of test lists that are split by name.
        # Now the order is status_id for test_name_groups, timestamp inside
        all_split_by_test_name.sort(key=lambda x: x[-1].testrail_status_id)

        # Fifth: Flatten list to send to TestRail
        sorted_results: List[ResultItem] = []
        for itemlist in all_split_by_test_name:
            for item in itemlist:
                sorted_results.append(item)

        return sorted_results
