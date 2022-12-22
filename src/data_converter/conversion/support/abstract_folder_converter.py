import logging
from abc import ABC, abstractmethod
from itertools import islice
from pathlib import Path
from typing import Iterable

from data_converter.conversion.support.types import FolderResult
from utilities.utilities.configuration.configuration import Config
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer


class AbstractFolderConverter(ABC):
    def __init__(self,
                 source_folder: Path,
                 destination: Path | Iterable[Path],
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
        pass  # STUB

    @abstractmethod
    def convert_folder(self):
        pass

    def _pre_conversion_actions(self):
        setup_logger(self._logger, self._logfile_path)
        self._timer.start_timer()

    def _post_conversion_actions(self, results: list[FolderResult]):
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
        limit: None | int,
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
