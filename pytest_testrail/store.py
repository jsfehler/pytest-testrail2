import json
import os
from typing import Any, Dict

from filelock import FileLock

from pytest import Config


class Store:
    """Store JSON data in a file. Keys can only be written to once.

    Store and associated JSON file exist to handle pytest-xdist's multiple
    sessions. Multiple sessions cause multiple instances of the plugin to be
    created. The only way to store state is to write to an external file.
    """

    def __init__(self, config: Config):
        self.config = config

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all the data currently in the store.

        Returns:
            dict
        """
        file_path = self.config.invocation_params.dir / 'store_pytest_testrail2.json'

        with FileLock(f'{file_path}.lock'):
            if file_path.is_file():
                data: Dict[str, Any] = json.loads(file_path.read_text())
                return data

        return {}

    def set_value(self, key: str, value: Any) -> None:
        """Set a variable into the store.

        Variables can only be placed into the store once. They should not be
        overwritten.

        Arguments:
            config: pytest.Config instance.
            key: The key to use in the store.
            value: The object to place in the store.
        """
        file_path = self.config.invocation_params.dir / 'store_pytest_testrail2.json'

        stored_value = self.get_all().get(key)
        if not stored_value:
            with FileLock(f'{file_path}.lock'):
                data = json.dumps({key: value})
                file_path.write_text(data)

        else:
            raise ValueError('Cannot set objects into a store multiple times.')

    def clear(self):
        """Remove the store files."""
        file_path = self.config.invocation_params.dir / 'store_pytest_testrail2.json'
        lock_path = self.config.invocation_params.dir / 'store_pytest_testrail2.json.lock'

        os.remove(file_path)
        os.remove(lock_path)
