from typing import Optional, Union

from pytest import Config

CONFIG_OPTION_TYPES = Union[str, bool, int, None]


class ConfigManager:
    """Handle retrieving configuration values.

    Config options set by the CLI take precedence over options set in the config file.

    Arguments:
        config (pytest.Config): Config object containing commandline flag options.
    """

    def __init__(self, config: Config):
        self.config = config

    def get(
        self,
        option_name: str = '',
        ini_name: str = '',
    ) -> CONFIG_OPTION_TYPES:
        """Get option from config.

        priority == cli > config file
        """
        rv: Optional[CONFIG_OPTION_TYPES] = None

        if ini_name:
            ini_value: CONFIG_OPTION_TYPES = self.config.getini(ini_name)
            if ini_value:
                rv = ini_value

        if option_name:
            option_value: CONFIG_OPTION_TYPES = self.config.getoption(option_name)
            if option_value:
                rv = option_value

        return rv
