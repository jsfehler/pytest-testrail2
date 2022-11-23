import base64
from typing import Optional, Union

import inori


class _TestRailAPI(inori.Client):
    """Client for the TestRailAPI."""

    route_paths = {
        'add_results_for_cases/${run_id}',
        'add_run/${project_id}',
        'close_run/${run_id}',
        'close_plan/${plan_id}',
        'get_run/${run_id}',
        'get_plan/${plan_id}',
        'get_tests/${run_id}',

    }

    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        timeout: Optional[Union[float, tuple[float, float]]] = 30,
    ):
        super().__init__(f'{base_url}/index.php?/api/v2/')

        self.user = user
        self.password = password

        self.timeout = timeout

        auth_as_bytes = base64.b64encode(
            bytes(f'{self.user}:{self.password}', 'utf-8'),
        )
        auth = str(auth_as_bytes, 'ascii').strip()

        self.headers['Content-Type'] = 'application/json'
        self.headers['Authorization'] = f'Basic {auth}'

    def validate_response(self, response: dict, strict: bool = False) -> None:
        """Get the error response from the TestRail API response.

        Arguments:
            response: Response from TestRail

        Returns:
            Union[None, str]: None or the error message.
        """
        error: Optional[str] = response.get('error', None)
        if error:
            self.logger.error(f'{error}')

            if strict:
                raise Exception(error)
