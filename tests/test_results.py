from pytest_testrail.results import Results


ASSIGN_USER_ID = 3
PROJECT_ID = 4
SUITE_ID = 1
TR_NAME = None


def test_add_results_sorting_different_name_same_case_id(api_client, new_resultitem):
    """Scenario:

    Given a collection of test results
    And multiple test results have the same case_id
    And those test results have different names
    And at least one test result has a failed status
    When testcases are published to TestRail
    Then results are published in the order of lowest to highest status_id
    """
    results = [
        new_resultitem(
            test_name="test_foo[alpha]",
            case_id=1234,
            status_id="passed",
            timestamp=8,
            comment='',
        ),
        new_resultitem(
            test_name="test_foo[omega]",
            case_id=1234,
            status_id="failed",
            timestamp=16,
            comment='',
        ),
        new_resultitem(
            test_name="test_foo[sigma]",
            case_id=1234,
            status_id="passed",
            timestamp=4,
            comment='',
        ),
    ]

    res = Results()
    for result in results:
        res.append(result)

    r2 = res._sort()

    expected_results = sorted(results, key=lambda x: x.testrail_status_id)

    assert r2 == expected_results


def test_add_results_sorting_same_name_most_recent_failed(api_client, new_resultitem):
    """Scenario:

    Given a collection of test results
    And multiple test results have the same case_id
    And those test results have the same name
    And no test results are from parametrized tets
    And the latest test result has a failed status
    When testcases are published to TestRail
    Then results are published in the order of timestamp
    """
    results = [
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            status_id="passed",
            timestamp=8,
            comment='',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            status_id="failed",
            timestamp=16,
            comment='',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            status_id="passed",
            timestamp=4,
            comment='',
        ),
    ]

    expected_results = sorted(results, key=lambda x: x.timestamp)

    res = Results()
    for result in results:
        res.append(result)

    r2 = res._sort()

    assert r2 == expected_results


def test_add_results_sorting_mixed_passed(api_client, new_resultitem):
    """Scenario:

    Given a collection of test results
    And multiple test results have the same case_id
    And at least one test result with the same case_id has a failed status
    And at least one test result has a different case_id with a passing status
    When testcases are published to TestRail
    Then results are published in the order of timestamp
    """
    results = [
        # 3rd run, passed
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        # Different case_id, ran at same time as newest
        new_resultitem(
            test_name="test_foo_2",
            case_id=5678,
            duration=0.1,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        # First run, blocked
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
        # Second run, failed
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=1,
            defects='PF-516',
            status_id="failed",
            timestamp=1,
            comment='this is comment',
        ),
    ]

    expected_results = [
        new_resultitem(
            test_name="test_foo_2",
            case_id=5678,
            duration=0.1,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=1,
            defects='PF-516',
            status_id="failed",
            timestamp=1,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
    ]

    res = Results()
    for result in results:
        res.append(result)

    r2 = res._sort()

    assert r2 == expected_results


def test_add_results_sorting_mixed_failed(api_client, new_resultitem):
    """Scenario:

    Given a collection of test results
    And multiple test results have the same case_id
    And at least one test result with the same case_id has a failed status
    And at least one test result has a different case_id with a failing status
    When testcases are published to TestRail
    Then results are published in the order of timestamp
    """
    results = [
        # 3rd run, passed
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        # Different case_id, ran at same time as newest
        new_resultitem(
            test_name="test_foo_2",
            case_id=5678,
            duration=0.1,
            status_id="failed",
            timestamp=9,
            comment='this is comment',
        ),
        # First run, blocked
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
        # Second run, failed
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=1,
            defects='PF-516',
            status_id="failed",
            timestamp=1,
            comment='this is comment',
        ),
    ]

    expected_results = [
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=1,
            defects='PF-516',
            status_id="failed",
            timestamp=1,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
        new_resultitem(
            test_name="test_foo_2",
            case_id=5678,
            duration=0.1,
            status_id="failed",
            timestamp=9,
            comment='this is comment',
        ),
    ]

    res = Results()
    for result in results:
        res.append(result)

    r2 = res._sort()

    assert r2 == expected_results


def test_add_results_sort_by_status_id_and_timestamp(api_client, new_resultitem):
    """Scenario:

    Given a collection of test results
    And multiple test results have the same case_id
    And multiple test results that are parametrized
    And at least one test result has a failed status
    When testcases are published to TestRail
    Then results are published in the order of: status_id, timestamp
    And failing testcases are published last
    And more recent results for the same status_id are published after older results
    """
    results = [
        # Parametrized test with 1 rerun
        new_resultitem(
            test_name='test_foo[alpha]',
            case_id=1234,
            duration=0.1,
            status_id="failed",
            timestamp=99,
            comment='this is comment',
            test_parametrize=['hypermode', 'alpha'],
        ),
        new_resultitem(
            test_name='test_foo[alpha]',
            case_id=1234,
            duration=0.1,
            status_id="passed",
            timestamp=124,
            comment='this is comment',
            test_parametrize=['hypermode', 'alpha'],
        ),
        # Parametrized test, other case
        new_resultitem(
            test_name='test_foo[beta]',
            case_id=1234,
            duration=0.1,
            status_id="passed",
            timestamp=500,
            comment='this is comment',
            test_parametrize=['hypermode', 'beta'],
        ),
        # Same ID as parametrized test.
        # Technically impossible but should be sorted regardless
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        # Different case_id, ran at same time as newest
        new_resultitem(
            test_name="test_foo_2",
            case_id=5678,
            duration=0.1,
            status_id="passed",
            timestamp=0.1,
            comment='this is comment',
        ),
        # Oldest, blocked
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
        # 2nd newest, failed
        new_resultitem(
            test_name="test_foo",
            case_id=1234,
            duration=1,
            defects='PF-516',
            status_id="failed",
            timestamp=1,
            comment='this is comment',
        ),
    ]

    expected_results = [
        new_resultitem(
            test_name='test_foo[alpha]',
            case_id=1234,
            duration=0.1,
            status_id="failed",
            timestamp=99,
            comment='this is comment',
            test_parametrize=['hypermode', 'alpha'],
        ),
        new_resultitem(
            test_name='test_foo[alpha]',
            case_id=1234,
            duration=0.1,
            status_id="passed",
            timestamp=124,
            comment='this is comment',
            test_parametrize=['hypermode', 'alpha'],
        ),
        new_resultitem(
            test_name='test_foo[beta]',
            case_id=1234,
            duration=0.1,
            status_id="passed",
            timestamp=500,
            comment='this is comment',
            test_parametrize=['hypermode', 'beta'],
        ),
        new_resultitem(
            test_name='test_foo_2',
            case_id=5678,
            duration=0.1,
            status_id="passed",
            timestamp=0.1,
            comment='this is comment',
        ),
        new_resultitem(
            test_name='test_foo',
            case_id=1234,
            duration=1,
            status_id="failed",
            defects='PF-516',
            timestamp=1,
            comment='this is comment',
        ),
        new_resultitem(
            test_name='test_foo',
            case_id=1234,
            duration=2.6,
            status_id="passed",
            timestamp=9,
            comment='this is comment',
        ),
        new_resultitem(
            test_name='test_foo',
            case_id=1234,
            duration=2.6,
            status_id="skipped",
            timestamp=16,
            comment='this is comment',
        ),
    ]

    res = Results()
    for result in results:
        res.append(result)

    r2 = res._sort()

    assert r2 == expected_results
