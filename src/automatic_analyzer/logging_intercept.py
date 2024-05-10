from __future__ import annotations
import inspect
import logging
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