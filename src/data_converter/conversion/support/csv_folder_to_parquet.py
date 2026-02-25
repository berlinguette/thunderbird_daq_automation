import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Union

import modin.pandas as modin_pd
import pandas as pd
from tqdm import tqdm

from data_converter.conversion.support.abstract_folder_converter import (
    AbstractFolderConverter,
)
from data_converter.conversion.support.constants import (
    SINGLE_CHANNEL_DATA_PREFIX,
    DUAL_CHANNEL_DATA_PREFIX,
)
from data_converter.conversion.support.csv_file_to_parquet import (
    DELIMITER,
    END_NUMBER_PATTERN,
    convert_csv_file_to_parquet,
    _get_split_data_destinations,
)
from data_converter.conversion.support.types import FolderResult
from data_converter.utilities.constants import BAR_FORMAT
from utilities.utilities.check_type import check_type, get_and_check
from utilities.utilities.configuration.configuration import Config


class AbstractCSVtoParquetFolderConverter(AbstractFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
        logger_name: str = "csv_to_parquet",
    ):
        super().__init__(
            source_folder, destination, config, logfile_path, logger_name=logger_name
        )

    def _convert_files_with_prefix(
        self, target_file_prefix: str, destination: Union[Path, Iterable[Path]]
    ) -> list[FolderResult]:
        num_files = self._config.get("files_limit")
        if num_files is not None:
            num_files = check_type(num_files, int, "files_limit")
        max_workers = get_and_check(self._config, int, "caen_tasks", 0)
        task_timeout = get_and_check(self._config, int, "caen_timeout", 0)
        small_files_support = get_and_check(self._config, bool, "small_files", False)
        text_ui = get_and_check(self._config, bool, "text_ui", False)

        # Filters csv files for only the ones with matching prefix
        filtered_source_files = [
            f
            for f in self._get_limited_files_with_extension(num_files, ".csv")
            if re.match(f"^{target_file_prefix}.*", f.name)
        ]

        folder_timeout = task_timeout * len(filtered_source_files)
        if folder_timeout == 0:
            folder_timeout = None

        if len(filtered_source_files) == 0:
            headers = []
            total_cols = 0
        else:
            first_file = [
                f
                for f in self._get_limited_files_with_extension(None, ".csv")
                if re.match(END_NUMBER_PATTERN, f.stem) is None
            ]
            if len(first_file) == 0:
                raise ValueError("Could not find csv file with headers")
            source_file = first_file[0]

            with open(source_file, "r") as openfile:
                header_line = openfile.readline()
                data_line = openfile.readline()
            headers = header_line.strip().split(DELIMITER)
            data_sample = data_line.strip().split(DELIMITER)
            total_cols = len(data_sample)

        results: list[FolderResult] = []
        with tqdm(
            desc="CSV Files",
            unit="file",
            total=len(filtered_source_files),
            bar_format=BAR_FORMAT,
            disable=not text_ui,
        ) as progress_bar:
            
            if small_files_support:  # eg. run in parallel
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    futures = [
                        ex.submit(
                            convert_csv_file_to_parquet,
                            source_file,
                            destination,
                            headers,
                            total_cols,
                            pd.read_csv,
                            self._logfile_path,
                        )
                        for source_file in filtered_source_files
                    ]
                    for future in as_completed(futures, timeout=folder_timeout):
                        result = future.result()
                        results.append(result)
                        progress_bar.update(1)
            else:
                for source_file in filtered_source_files:
                    result = convert_csv_file_to_parquet(
                        source_file,
                        destination,
                        headers,
                        total_cols,
                        modin_pd.read_csv,
                        self._logfile_path,
                    )
                    results.append(result)
                    progress_bar.update(1)

        return results


class SingleChannelCSVConverter(AbstractCSVtoParquetFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Path | Iterable[Path],
        config: Config,
        logfile_path: Path,
        logger_name: str = "csv_to_parquet_single",
    ):
        super().__init__(source_folder, destination, config, logfile_path, logger_name)

    def convert_folder(self):
        self._pre_conversion_actions()
        results = self._convert_files_with_prefix(
            SINGLE_CHANNEL_DATA_PREFIX, self._destination
        )
        self._post_conversion_actions(results)


class DualChannelCSVConverter(AbstractCSVtoParquetFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Path | Iterable[Path],
        config: Config,
        logfile_path: Path,
        logger_name: str = "csv_to_parquet_double",
    ):
        super().__init__(source_folder, destination, config, logfile_path, logger_name)

    def convert_folder(self):
        self._pre_conversion_actions()

        ch0_dest = self._get_path_with_channel_appended("ch0")
        self._make_dir_at_paths(ch0_dest)
        ch0_results = self._convert_files_with_prefix(
            f"{DUAL_CHANNEL_DATA_PREFIX}0", ch0_dest
        )

        ch1_dest = self._get_path_with_channel_appended("ch1")
        self._make_dir_at_paths(ch1_dest)
        ch1_results = self._convert_files_with_prefix(
            f"{DUAL_CHANNEL_DATA_PREFIX}1", ch1_dest
        )

        self._post_conversion_actions(ch0_results + ch1_results)

    def _get_path_with_channel_appended(self, channel_folder: str) -> Iterable[Path]:
        destinations = _get_split_data_destinations(self._destination)

        appended_paths = [Path(dest, channel_folder) for dest in destinations]
        return appended_paths

    def _make_dir_at_paths(self, destination: Iterable[Path]):
        for path in destination:
            path.mkdir(parents=True, exist_ok=True)