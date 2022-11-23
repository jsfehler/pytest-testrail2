class MockResponse:
    """Mock the Response object from requests."""

    def __init__(self, expected):
        self.expected = expected

    def json(self) -> dict:
        return self.expected


TESTPLAN = {
    "id": 58,
    "is_completed": False,
    "entries": [
        {
            "id": "ce2f3c8f-9899-47b9-a6da-db59a66fb794",
            "name": "Test Run 5/23/2017",
            "runs": [
                {
                    "id": 59,
                    "name": "Test Run 5/23/2017",
                    "is_completed": False,
                },
            ],
        },
        {
            "id": "084f680c-f87a-402e-92be-d9cc2359b9a7",
            "name": "Test Run 5/23/2017",
            "runs": [
                {
                    "id": 60,
                    "name": "Test Run 5/23/2017",
                    "is_completed": True,
                },
            ],
        },
        {
            "id": "775740ff-1ba3-4313-a9df-3acd9d5ef967",
            "name": "Test Run 5/23/2017",
            "runs": [
                {
                    "id": 61,
                    "is_completed": False,
                },
            ],
        },
    ]
}

get_plan_response = MockResponse(TESTPLAN)
