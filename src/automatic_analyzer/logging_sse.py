import inspect
import logging
from loguru import logger
import queue


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


class SSEAnnouncer:
    """
    Pub/sub implementation for use with SSE.
    SSE endpoints subscribe by listening and watching their queue for new messages.
    New messages are added by announcing with the data and optional event
    """
    def __init__(self):
        self.listeners: list[queue.Queue] = []

    def listen(self):
        """
        Each listener gets its own message queue that it can sequentially read from
        """
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def announce(self, data: str, event: str | None = None):
        """
        All listeners will have msg inserted into their listening queue.
        If any listener's queue is full they are assumed to no longer be listening and are removed
        """
        for i in reversed(range(len(self.listeners))):
            try:
                msg = self._format_sse(data, event)
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

    def _format_sse(self, data: str, event: str | None) -> str:
        msg = f"data: {data}\n\n"
        if event is not None:
            msg = f"event: {event}\n{msg}"
        return msg
