import logging
from pathlib import Path
from typing import Tuple

from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              setup_logger)


def get_conversion_logfile_path(destination: Path) -> Path:
    """Gives correct conversion log file path for given experiment folder

    Parameters
    ----------
    experiment_folder : Path
        path to root folder for this experiment

    Returns
    -------
    Path
        path to experiment's conversion log file
    """
    log_filename = 'conversion.log'
    if destination.is_dir():
        return destination / log_filename
    else:
        return destination.parent / log_filename


def set_up_file_logging(
    source_file: Path,
    logfile_path: Path
) -> Tuple[logging.Logger, Messenger]:
    """Sets up a logger to track conversion progress for a new file
    
    Parameters
    ----------
    source_file : Path
        Path to the source file to track
    logfile_path : Path
        Path to file to store logs in
    """
    source_name = source_file.name
    new_logger = logging.getLogger(f'proc-{source_name}')
    setup_logger(new_logger, logfile_path)
    new_messenger = Messenger(new_logger, on_screen=False)
    new_messenger.debug(f"Converting {source_name}...")
    return new_logger, new_messenger
