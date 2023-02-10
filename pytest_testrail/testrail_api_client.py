from typing import Any, Dict, List, Optional, Tuple, Union

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
        auth=None,
        timeout: Optional[Union[float, Tuple[float, float]]] = 30.0,
        verify: Optional[bool] = True,
    ):
        super().__init__(f'{base_url}/index.php?/api/v2/', auth)

        self.request_kwargs['timeout'] = timeout
        self.request_kwargs['verify'] = verify

        self.headers['Content-Type'] = 'application/json'

    def validate_response(
        self,
        response: Union[List[Any], Dict[str, Any]],
        strict: bool = False,
    ) -> None:
        """Get the error response from the TestRail API response.

        Arguments:
            response: Response from TestRail

        Returns:
            Union[None, str]: None or the error message.
        """
        # Response from TestRail may be a list.
        # If a list, it won't have an error.
        if isinstance(response, dict):
            error: Optional[str] = response.get('error', None)
            if error:
                self.logger.error(f'{error}')

                if strict:
                    raise Exception(error)
