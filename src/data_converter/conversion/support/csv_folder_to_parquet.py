import re
from itertools import repeat
from pathlib import Path
from typing import Iterable

import modin.pandas as modin_pd
import pandas as pd
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from data_converter.conversion.support.abstract_folder_converter import \
    AbstractFolderConverter
from data_converter.conversion.support.csv_file_to_parquet import (
    DELIMITER, END_NUMBER_PATTERN, convert_csv_file_to_parquet)
from data_converter.utilities.constants import BAR_FORMAT
from utilities.utilities.check_type import check_type, get_and_check
from utilities.utilities.configuration.configuration import Config


class CSVtoParquetFolderConverter(AbstractFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Path | Iterable[Path],
        config: Config,
        logfile_path: Path,
        logger_name: str = 'csv_to_parquet'
    ):
        super().__init__(
            source_folder, destination, config, logfile_path,
            logger_name=logger_name)

    def convert_folder(self):
        self._pre_conversion_actions()

        num_files = self._config.get('files_limit')
        if num_files is not None:
            num_files = check_type(num_files, int, 'files_limit')
        csv_workers = get_and_check(self._config, int, 'csv_tasks', 0)
        csv_timeout = get_and_check(self._config, int, 'csv_timeout', 0)
        large_files_support = get_and_check(
            self._config, bool, 'large_files', False)

        source_files = [
            f for f in self._get_limited_files_with_extension(
                num_files, '.csv'
            )
        ]

        csv_timeout = csv_timeout * len(source_files)
        if csv_timeout == 0:
            csv_timeout = None

        if len(source_files) == 0:
            headers = []
            total_cols = 0
        else:
            first_file = [
                f for f
                in self._get_limited_files_with_extension(None, '.csv')
                if re.match(END_NUMBER_PATTERN, f.stem) is None
            ]
            if len(first_file) == 0:
                raise ValueError('Could not find csv file with headers')
            source_file = first_file[0]

            with open(source_file, 'r') as openfile:
                header_line = openfile.readline()
                data_line = openfile.readline()
            headers = header_line.strip().split(DELIMITER)
            data_sample = data_line.strip().split(DELIMITER)
            total_cols = len(data_sample)

        if large_files_support:
            results = []
            with tqdm(
                desc='CSV Files',
                unit='file',
                total=len(source_files),
                bar_format=BAR_FORMAT
            ) as progress_bar:
                for source_file in source_files:
                    result = convert_csv_file_to_parquet(
                        source_file,
                        self._destination,
                        headers,
                        total_cols,
                        modin_pd.read_csv,
                        self._logfile_path
                    )
                    progress_bar.update()
                    results.append(result)
        else:
            results = thread_map(
                convert_csv_file_to_parquet,
                source_files,
                repeat(self._destination),
                repeat(headers),
                repeat(total_cols),
                repeat(pd.read_csv),
                repeat(self._logfile_path),
                timeout=csv_timeout,
                max_workers=csv_workers,
                desc='CSV files',
                unit='file',
                total=len(source_files),
                bar_format=BAR_FORMAT
            )

        self._post_conversion_actions(results)
