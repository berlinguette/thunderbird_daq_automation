from concurrent.futures import ThreadPoolExecutor, as_completed
from math import floor
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import pandas as pd
from tqdm import tqdm

from data_converter.conversion.support.abstract_folder_converter import (
    AbstractFolderConverter,
)
from data_converter.conversion.support.bin_file_to_parquet import (
    END_NUMBER_PATTERN,
    convert_bin_file_to_parquet,
)
from data_converter.conversion.support.types import FolderResult
from data_converter.utilities.constants import BAR_FORMAT
from data_converter.utilities.destination_file_name import get_destination_file_name
from data_converter.utilities.df_mem_usage import get_df_dict_mem_usage
from data_converter.utilities.first_file import get_first_source_file
from data_converter.utilities.save_to_parquet import save_to_parquet
from data_converter.utilities.split_list import split_list_by_count
from utilities.utilities.check_type import check_type, get_and_check
from utilities.utilities.configuration.configuration import Config


class BINtoParquetFolderConverter(AbstractFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
        logger_name: str = "folder_converter",
    ):
        super().__init__(
            source_folder, destination, config, logfile_path, logger_name=logger_name
        )

    def convert_folder(self):
        self._pre_conversion_actions()

        num_files = self._config.get("files_limit")
        if num_files is not None:
            num_files = check_type(num_files, int, "files_limit")
        max_workers = get_and_check(self._config, int, "caen_tasks", 0)
        task_timeout = get_and_check(self._config, int, "caen_timeout", 0)
        mem_use_threshold = get_and_check(self._config, int, "mem_use_threshold", 0)
        text_ui = get_and_check(self._config, bool, "text_ui", False)

        source_files = [
            f for f in self._get_limited_files_with_extension(num_files, ".bin")
        ]
        first_file = get_first_source_file(source_files, END_NUMBER_PATTERN)

        folder_timeout = task_timeout * len(source_files)
        if folder_timeout == 0:
            folder_timeout = None
        results: List[FolderResult] = []
        with tqdm(
            total=len(source_files),
            desc="BIN files",
            unit="file",
            bar_format=BAR_FORMAT,
            disable=not text_ui,
        ) as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                index = 0
                sample_files, remaining = split_list_by_count(source_files, max_workers)
                sample_folder_results, dfs = self._convert_some_files(
                    ex, sample_files, pbar, task_timeout
                )
                results.extend(sample_folder_results)
                if mem_use_threshold == 0:
                    batch_size = len(source_files)
                else:
                    df_dict_mem_usage = [
                        get_df_dict_mem_usage(df_dict) for _, df_dict in dfs
                    ]
                    total_mem_usage = sum(df_dict_mem_usage)
                    avg_mem_usage = total_mem_usage / len(sample_files)
                    batch_size = floor(mem_use_threshold / avg_mem_usage)
                    batch_size = 1 if batch_size < 1 else batch_size
                count_remaining = batch_size - len(sample_files)

                if len(remaining) > 0 and count_remaining >= 1:
                    remaining_in_batch, remaining = split_list_by_count(
                        remaining, count_remaining
                    )
                    batch_results, batch_dfs = self._convert_some_files(
                        ex, remaining_in_batch, pbar, task_timeout
                    )
                    results.extend(batch_results)
                    dfs.extend(batch_dfs)

                dfs.sort(key=lambda x: x[0])
                dfs = [df_dict for _, df_dict in dfs]
                psd_file_name = get_destination_file_name(first_file, index, "psd")
                signals_file_name = get_destination_file_name(
                    first_file, index, "signals"
                )
                save_to_parquet(dfs, 'pandas', "psd", self._psd_dest / psd_file_name)
                save_to_parquet(dfs, 'pandas', "signals", self._signals_dest / signals_file_name)

                while len(remaining) > 0:
                    index += 1
                    batch_files, remaining = split_list_by_count(remaining, batch_size)
                    batch_results, batch_dfs = self._convert_some_files(
                        ex, batch_files, pbar, task_timeout
                    )
                    results.extend(batch_results)

                    batch_dfs.sort(key=lambda x: x[0])
                    batch_dfs = [df_dict for _, df_dict in dfs]

                    psd_file_name = get_destination_file_name(first_file, index, "psd")
                    signals_file_name = get_destination_file_name(
                        first_file, index, "signals"
                    )
                    save_to_parquet(dfs, 'pandas', "psd", self._psd_dest / psd_file_name)
                    save_to_parquet(
                        dfs, 'pandas', "signals", self._signals_dest / signals_file_name
                    )

        self._post_conversion_actions(results)

    def _convert_some_files(
        self,
        ex: ThreadPoolExecutor,
        source_files: List[Path],
        pbar: tqdm,
        task_timeout: float,
    ) -> Tuple[List[FolderResult], List[Tuple[str, Dict[str, pd.DataFrame]]]]:
        results: List[FolderResult] = []
        dfs: List[Tuple[str, Dict[str, pd.DataFrame]]] = []
        futures = [
            ex.submit(convert_bin_file_to_parquet, source_file, self._logfile_path)
            for source_file in source_files
        ]
        timeout = task_timeout * len(futures)
        for future in as_completed(futures, timeout=timeout):
            result, df_dict = future.result()
            _, source_file_name = result
            results.append(result)
            if df_dict is not None:
                dfs.append((source_file_name, df_dict))
            pbar.update(1)
        return results, dfs
