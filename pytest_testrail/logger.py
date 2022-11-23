import logging
import uuid


def get_logger() -> logging.Logger:
    """Get a new instance of the plugin logger."""
    logger_name = f"{__name__} {str(uuid.uuid4())}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    logging_formatter = logging.Formatter('%(asctime)s - [testrail] - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(logging_formatter)

    logger.addHandler(handler)

    return logger
