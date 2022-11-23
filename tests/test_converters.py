from pytest_testrail import converters


def test_clean_test_ids():
    assert list(converters.clean_test_ids(['C1234', 'C12345'])) == [1234, 12345]
