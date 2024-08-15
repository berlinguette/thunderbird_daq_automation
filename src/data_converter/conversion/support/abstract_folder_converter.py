import logging
from abc import ABC, abstractmethod
from itertools import islice
from pathlib import Path
from typing import Iterable, List, Optional, Union

from data_converter.conversion.support.types import FolderResult
from utilities.utilities.configuration.configuration import Config
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer


class AbstractFolderConverter(ABC):
    """Represents a folder converter that can take a source folder
    and transform all files in it before saving to some destination.

    Parameters
    ----------
    source_folder : Path
        Path to the folder where the source files can be found
    destination : Path
        Path to the destination folder where converted files will be stored
    config : Config
        Configuration data. See configuration.py for more info
    logfile_path : Path
        Path to logfile
    logger_name : str
        Name to use for the logger
    """
    def __init__(self,
                 source_folder: Path,
                 destination: Union[Path, Iterable[Path]],
                 config: Config,
                 logfile_path: Path,
                 logger_name: str = 'folder_converter'):
        self._source_folder = source_folder
        self._destination = destination
        self._config = config
        self._logfile_path = logfile_path

        self._logger = logging.Logger(logger_name)
        self._messenger = Messenger(self._logger)
        self._log_only_messenger = Messenger(self._logger, on_screen=False)
        self._timer = Timer()

    @abstractmethod
    def convert_folder(self):
        """Performs the conversion with the parameters given upon initialization of the class."""
        pass

    def _pre_conversion_actions(self):
        setup_logger(self._logger, self._logfile_path)
        self._timer.start_timer()

    def _post_conversion_actions(self, results: List[FolderResult]):
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

    def _get_limited_files_with_extension(
        self,
        limit: Optional[int],
        extension: str
    ) -> Iterable[Path]:
        ext_files_generator = (file for file in self._source_folder.iterdir()
                               if file.is_file()
                               and file.suffix.lower() == extension)
        if limit is None or limit == 0:
            files = ext_files_generator
        else:
            files = islice(ext_files_generator, limit)
        return files
