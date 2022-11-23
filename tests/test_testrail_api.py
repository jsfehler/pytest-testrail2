import pytest

from pytest_testrail.testrail_api_client import _TestRailAPI


def test_get_api_error(caplog):
    client = _TestRailAPI('dummy', 'a', 'b')
    response = {'error': 'ded'}
    client.validate_response(response)

    assert caplog.record_tuples[0][2] == 'ded'


def test_get_api_error_strict():
    client = _TestRailAPI('dummy', 'a', 'b')
    response = {'error': 'ded'}

    with pytest.raises(Exception) as exc:
        client.validate_response(response, strict=True)

    assert str(exc.value) == 'ded'
