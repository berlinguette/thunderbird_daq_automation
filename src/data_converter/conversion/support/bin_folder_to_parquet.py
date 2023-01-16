from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Union

from tqdm import tqdm

from data_converter.conversion.support.abstract_folder_converter import \
    AbstractFolderConverter
from data_converter.conversion.support.bin_file_to_parquet import \
    convert_bin_file_to_parquet
from data_converter.conversion.support.types import FolderResult
from data_converter.utilities.constants import BAR_FORMAT
from utilities.utilities.check_type import check_type, get_and_check
from utilities.utilities.configuration.configuration import Config


class BINtoParquetFolderConverter(AbstractFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
        logger_name: str = 'folder_converter'
    ):
        super().__init__(source_folder,
                         destination,
                         config,
                         logfile_path,
                         logger_name=logger_name)

    def convert_folder(self):
        self._pre_conversion_actions()

        num_files = self._config.get('files_limit')
        if num_files is not None:
            num_files = check_type(num_files, int, 'files_limit')
        max_workers = get_and_check(self._config, int, 'caen_tasks', 0)
        task_timeout = get_and_check(self._config, int, 'caen_timeout', 0)
        mem_use_threshold = get_and_check(
            self._config, int, 'mem_use_threshold', 0)

        source_files = [
            f for f in self._get_limited_files_with_extension(
                num_files, '.bin'
            )
        ]

        folder_timeout = task_timeout * len(source_files)
        if folder_timeout == 0:
            folder_timeout = None
        if mem_use_threshold == 0:
            mem_use_threshold = None
        results: list[FolderResult] = []
        with tqdm(total=len(source_files),
                  desc='BIN files',
                  unit='file',
                  bar_format=BAR_FORMAT) as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = [
                    ex.submit(
                        convert_bin_file_to_parquet,
                        source_file,
                        self._destination,
                        self._logfile_path,
                        mem_use_threshold)
                    for source_file in source_files]
                for future in as_completed(futures,
                                           timeout=folder_timeout):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)

        self._post_conversion_actions(results)
