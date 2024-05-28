from __future__ import annotations
import inspect
import logging
import time
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    Intercepts normal Python logging logs and converts them to loguru logs
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def log_stream_filter(record) -> bool:
    """
    Filters out unnecessary log messages to streamline logs sent to frontend interface
    """
    if "werkzeug" in record["name"] or record["module"] == "sh":
        return False
    return True


def follow(file, sleep_sec=0.1):
    """ Yield each line from a file as they are written.
    `sleep_sec` is the time to sleep after empty reads. """
    line = ''
    while True:
        tmp = file.readline()
        if tmp is not None and tmp != "":
            line += tmp
            if line.endswith("\n"):
                yield line
                line = ''
        elif sleep_sec:
            time.sleep(sleep_sec)