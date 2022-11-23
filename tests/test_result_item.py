from pytest_testrail.status import PYTEST_TO_TESTRAIL_STATUS


def test_resultitem_status_id_success(new_resultitem):
    result_item = new_resultitem(status_id='passed')

    assert result_item.testrail_status_id == PYTEST_TO_TESTRAIL_STATUS['passed']


def test_resultitem_status_id_failed(new_resultitem):
    result_item = new_resultitem(status_id='failed')

    assert result_item.testrail_status_id == PYTEST_TO_TESTRAIL_STATUS['failed']


def test_resultitem_as_api_payload_parametrize(new_resultitem):
    result_item = new_resultitem(
        case_id=1950,
        status_id="passed",
        comment="Success.",
        timestamp=1,
        duration=0.1,
        test_parametrize={'foo': 1}
    )

    data = result_item.as_api_payload()

    expected_comment = "# Test parametrize: #\n{'foo': 1}\n\n"

    assert expected_comment in data['comment']


def test_resultitem_as_api_payload_truncated_comment(new_resultitem):
    padding = ','.join([str(i) for i in range(4000)])

    result_item = new_resultitem(
        case_id=1950,
        status_id="passed",
        comment=padding,
        timestamp=1,
        duration=0.1,
        test_parametrize={'foo': 1}
    )

    data = result_item.as_api_payload()

    assert 'Log truncated\n...\n' in data['comment']
