from abc import ABC, abstractmethod
from pathlib import Path
import logging

from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)

class AbstractFileConverter(ABC):
    def __init__(self, destination_folder: Path, logfile_path: Path):
        self._dest_folder = destination_folder
        self._logfile_path = logfile_path
        pass  # STUB
    
    @abstractmethod
    def convert_file(self, source_file: Path):
        pass
    
    def _set_up_file_logging(
        self, 
        source_file: Path, 
        logfile_path: Path
    ) -> tuple[logging.Logger, Messenger]:
        source_name = source_file.name
        logger = logging.getLogger(f'proc-{source_name}')
        setup_logger(logger, self._logfile_path)
        messenger = Messenger(logger, on_screen=False)
        messenger.debug(f"Converting {source_name}...")
        return logger, messenger
    