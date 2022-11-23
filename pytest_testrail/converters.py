import re
from typing import Any, List, Tuple, Union


def clean_test_ids(test_ids: Union[Tuple[str], Any]) -> List[int]:
    """Clean pytest marker containing testrail testcase ids.

    Attributes:
        test_ids (tuple[str]):

    Returns:
        list[int]: test_ids.
    """
    rv = []

    pattern = '(?P<test_id>[0-9]+$)'

    for test_id in test_ids:
        match = re.search(pattern, test_id)
        if match:
            clean_test_id: str = match.groupdict().get('test_id')
            rv.append(int(clean_test_id))

    return rv


def clean_test_defects(defect_ids: Union[Tuple[str], Any]) -> List[str]:
    """Clean pytest marker containing testrail defects ids.

    Attributes:
        defect_ids (tuple[str]):

    Returns:
        list[str]: defect_ids.
    """
    rv = []

    pattern = '(?P<defect_id>.*)'

    for defect_id in defect_ids:
        match = re.search(pattern, defect_id)
        if match:
            clean_defect_id: str = match.groupdict().get('defect_id')
            rv.append(clean_defect_id)

    return rv
