import json
import os
from typing import Any, Dict

from filelock import FileLock

from pytest import Config


class Store:
    """Handle the storing of JSON data in a file.

    Keys can only be written to once. If a key exists in the store file and
    an attempt is made to set it then a ValueError will be raised.

    Store() and associated JSON file exist to handle pytest-xdist's multiple
    sessions. Multiple sessions cause multiple instances of the plugin to be
    created. The only way to store state is to write to an external file.

    Thus, the first xdist node to write to the store determines the value for
    the rest.

    Arguments:
        config: pytest.Config instance.
    """

    def __init__(self, config: Config):
        self.config = config

        self.name = 'store_pytest_testrail2'

        self.file_path = self.config.invocation_params.dir / f'{self.name}.json'
        self.lock_path = self.config.invocation_params.dir / f'{self.name}.json.lock'

        # The lock prevents multiple test nodes from read/writing simultaneously
        self.lock = FileLock(f'{self.lock_path}')

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all the data currently in the store.

        Returns:
            dict
        """
        with self.lock:
            if self.file_path.is_file():
                data: Dict[str, Any] = json.loads(self.file_path.read_text())
                return data

        return {}

    def set_value(self, key: str, value: Any) -> None:
        """Set a variable into the store.

        Variables can only be placed into the store once.

        Arguments:
            key: The key to use in the store.
            value: The object to place in the store.

        Raises:
            ValueError: If a value would be overwritten.
        """
        stored_value = self.get_all().get(key)
        if not stored_value:
            with self.lock:
                data = json.dumps({key: value})
                self.file_path.write_text(data)

        else:
            raise ValueError('Cannot set objects into a store multiple times.')

    def clear(self) -> None:
        """Remove the store and lock files.

        The Store() class does not guarantee the store file is created.
        If the store file does not exist and Store().clear() is called,
        it will be gracefully ignored.
        """
        try:
            os.remove(self.file_path)
        except OSError:
            pass

        try:
            os.remove(self.lock_path)
        except OSError:
            pass
