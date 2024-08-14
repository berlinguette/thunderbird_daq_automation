from pathlib import Path
import logging
import pandas as pd
import re
import tarfile

from pydantic import FilePath
from utilities.utilities.logging_helpers.setup_logger import (
    Messenger,
    setup_logger,
    cleanup_logger,
)
from utilities.utilities.timing import Timer

logger = logging.getLogger("reactor_data_to_parquet")
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)
archive_pattern = re.compile(r".+_\d{8}-\d{9}_data")
data_file_pattern = re.compile(r"ID-\S. (.+) (\d+)")


def convert_reactor_data_to_parquet(
    source: Path, destination: Path, logfile_path: Path
):
    setup_logger(logger, logfile_path)
    log_only_messenger.debug(f"Starting reactor data conversion in {source.name}")
    timer = Timer(start_now=True)

    reactor_data_matches = [
        file_path
        for file_path in source.iterdir()
        if _is_reactor_data_archive(file_path)
    ]
    if len(reactor_data_matches) < 1:
        raise ValueError(f"No reactor data archive files found in {source}")
    reactor_data_path = reactor_data_matches[0]
    log_only_messenger.debug(f"Found reactor data archive at {reactor_data_path}")

    # TODO scan tarfile for each device/parameter csv file set and process
    with tarfile.open(reactor_data_path, "r:*") as reactor_tar:
        all_filenames = [x for x in reactor_tar.getnames()]
    # TODO csv -> pandas
    # TODO save to parquet in destination folder
    exec_time = timer.stop_timer()
    formatted_time = timer.format_elapsed_time(exec_time, decimals=4)
    messenger.info("Reactor data processed")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")
    cleanup_logger(logger)


def _is_reactor_data_archive(file_path: Path) -> bool:
    is_tar = "tar" in file_path.suffixes
    is_gzip = "gz" in file_path.suffixes
    name_pattern_match = archive_pattern.match(file_path.name)
    return file_path.is_file() and is_tar and is_gzip and name_pattern_match is not None
