import logging
from abc import ABC, abstractmethod
from pathlib import Path

from utilities.utilities.configuration.configuration import Config
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer

ConversionResult = tuple[bool, str]

class AbstractFolderConverter(ABC):
    def __init__(self, 
                 source_folder: Path, 
                 destination_folder: Path,
                 logger_name: str, 
                 logfile_path: Path):
        self._source_folder = source_folder
        self._logfile_path = logfile_path
        
        self._logger = logging.Logger(logger_name)
        self._messenger = Messenger(self._logger)
        self._log_only_messenger = Messenger(self._logger, on_screen=False)
        self._timer = Timer()
        pass  # STUB
    
    @abstractmethod
    def convert_folder(self):
        pass
    
    def _pre_conversion_actions(self):
        setup_logger(self._logger, self._logfile_path)
        self._timer.start_timer()
        
    def _post_conversion_actions(self, results: list[ConversionResult]):
        exec_time = self._timer.stop_timer()
        formatted_time = self._timer.format_elapsed_time(exec_time, decimals=4)
        good_results = [filename for worked, filename in results if worked]
        bad_results = [filename for worked, filename in results if not worked]
        self._messenger.info(f"Processed {len(results)} files")
        self._messenger.info(f"{len(good_results)} successful conversions")
        self._messenger.info(f"{len(bad_results)} were unsuccessful. " + 
                             "See logs for more information")
        self._log_only_messenger.debug("Failing files:")
        for result in bad_results:
            self._log_only_messenger.debug(f"     {result}")
        self._log_only_messenger.debug(f"Elapsed time: {formatted_time}")
        cleanup_logger(self._logger)
        
        
        