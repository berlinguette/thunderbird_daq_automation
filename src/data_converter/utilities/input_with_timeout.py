import multiprocessing
import os
import sys
from typing import Any, TypeVar

T = TypeVar("T")


def input_with_timeout(prompt: str, timeout: int | None = None) -> str:
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_input_with_timeout_process, args=(sys.stdin.fileno(), queue, prompt)
    )
    process.start()
    try:
        process.join(timeout)
        if process.is_alive():
            raise ValueError(f"Timed out after {timeout} seconds")
        return queue.get()
    finally:
        process.terminate()


def _input_with_timeout_process(
    stdin_file_descriptor: int | Any, queue: multiprocessing.Queue, prompt: str
):
    sys.stdin = os.fdopen(stdin_file_descriptor)
    queue.put(input(prompt))
