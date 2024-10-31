from __future__ import absolute_import, unicode_literals

"""Custom logger configuration."""
from logging import Logger
from sys import stdout

from loguru import logger as custom_logger # type: ignore


def log_formatter(record: dict) -> str:
    """
    The function `log_formatter` formats log records based on their log level for a custom logger.

    :param record: The `record` parameter in the `log_formatter` function is a dictionary containing log
    metadata and message. It is used to format log records based on the log level specified in the
    record. The function returns a formatted string based on the log level present in the record
    :type record: dict
    :return: The `log_formatter` function returns a formatted string based on the log level specified in
    the input `record` dictionary. The format includes the timestamp, log level, and message in
    different colors based on the log level.
    """
    if record["level"].name == "TRACE":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #cfe2f3>{level}</fg #cfe2f3>: <light-white>{message}</light-white>\n"
    elif record["level"].name == "INFO":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #9cbfdd>{level}</fg #9cbfdd>: <light-white>{message}</light-white>\n"
    elif record["level"].name == "DEBUG":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #8598ea>{level}</fg #8598ea>: <light-white>{message}</light-white>\n"
    elif record["level"].name == "WARNING":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> |  <fg #dcad5a>{level}</fg #dcad5a>: <light-white>{message}</light-white>\n"
    elif record["level"].name == "SUCCESS":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #3dd08d>{level}</fg #3dd08d>: <light-white>{message}</light-white>\n"
    elif record["level"].name == "ERROR":
        return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #ae2c2c>{level}</fg #ae2c2c>: <light-white>{message}</light-white>\n"
    return "<fg #70acde>{time:MM-DD-YYYY HH:mm:ss}</fg #70acde> | <fg #b3cfe7>{level}</fg #b3cfe7>: <light-white>{message}</light-white>\n"

def create_logger() -> Logger: # type: ignore
    """
    The function `create_logger` sets up a custom logger with specific configurations.
    :return: The function `create_logger` is returning a custom logger object after removing any
    existing logger, adding a new logger that outputs to standard output with colorization and a
    specific log format, and then returning this custom logger object.
    """
    custom_logger.remove()
    custom_logger.add(stdout, colorize=True, format=log_formatter)
    return custom_logger


# `LOGGER = create_logger()` is creating a custom logger object with specific configurations. This
# custom logger is set up to output log messages to the standard output (stdout) with colorization
# based on the log level and a specific log format defined in the `log_formatter` function. The
# `create_logger` function removes any existing logger, adds a new logger with the specified
# configurations, and then returns this custom logger object.
LOGGER: Logger = create_logger()
