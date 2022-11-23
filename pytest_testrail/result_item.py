from dataclasses import dataclass
from typing import List, Optional

from .status import PYTEST_TO_TESTRAIL_STATUS


@dataclass
class ResultItem:
    """Representation of a single test result.

    Attributes:
        test_name: Pytest name for the test.
        case_id: TestRail case_id field.
        status_id: Pytest result status.
        duration: Time taken to run the test.
        comment: TestRail comment field.
        defects: TestRail defects field.
        test_parametrize: Parameters used in the test.
        timestamp: Time of when the ResultItem was created.
    """

    test_name: str
    case_id: int
    status_id: str
    duration: float
    comment: Optional[str]
    defects: Optional[str]
    test_parametrize: Optional[List[str]]
    timestamp: float

    @property
    def testrail_status_id(self) -> int:
        """Get the result status in testrail format.

        Returns:
            int
        """
        return PYTEST_TO_TESTRAIL_STATUS[self.status_id]

    def as_api_payload(
        self,
        custom_comment: Optional[str] = '',
        comment_size_limit: int = 4000,
    ) -> dict:
        """Get this object in a form suitable to use in an API payload."""
        rv: dict = {
            'status_id': self.testrail_status_id,
            'case_id': self.case_id,
            'defects': self.defects,
            'elapsed': '',
            'comment': '',
        }

        duration = self.duration
        if duration:
            # TestRail API doesn't handle milliseconds
            duration = 1 if (duration < 1) else int(round(duration))
            rv['elapsed'] = f"{str(duration)}s"

        # Handle comments
        comment_header = '# Pytest result: #\n'

        if custom_comment:
            custom_comment = f"{custom_comment}\n"

        test_output = ''
        if self.comment:
            test_output = f"    {self.comment}\n"

        _comment = f"{comment_header}{custom_comment}{test_output}"

        # Add parametrize info, if applicable.
        test_parametrize = self.test_parametrize
        if test_parametrize:
            parametrize_msg = (
                "# Test parametrize: #"
                "\n"
                f"{str(test_parametrize)}"
                "\n\n"
            )
            _comment += parametrize_msg

        # Truncate comment if necessary.
        # Indent text to avoid string formatting by TestRail.
        truncated_msg = 'Log truncated\n...\n'
        truncate_amount = len(truncated_msg) + comment_size_limit

        truncated_comment = _comment[-truncate_amount:].replace('\n', '\n    ')

        if len(truncated_comment) >= truncate_amount:
            _comment = f'    {truncated_msg}{truncated_comment}'

        rv['comment'] = _comment
        return rv
