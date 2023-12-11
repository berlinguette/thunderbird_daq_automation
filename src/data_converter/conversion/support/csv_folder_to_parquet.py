from concurrent.futures import ThreadPoolExecutor, as_completed
from math import floor
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import modin.pandas as modin_pd
import pandas as pd
from tqdm import tqdm

from data_converter.conversion.support.abstract_folder_converter import (
    AbstractFolderConverter,
)
from data_converter.conversion.support.csv_file_to_parquet import (
    DELIMITER,
    END_NUMBER_PATTERN,
    convert_csv_file_to_df,
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


class CSVtoParquetFolderConverter(AbstractFolderConverter):
    def __init__(
        self,
        source_folder: Path,
        destination_folder: Union[Path, Iterable[Path]],
        config: Config,
        logfile_path: Path,
        logger_name: str = "csv_to_parquet",
    ):
        super().__init__(
            source_folder,
            destination_folder,
            config,
            logfile_path,
            logger_name=logger_name,
        )

    def convert_folder(self):
        self._pre_conversion_actions()

        num_files = self._config.get("files_limit")
        if num_files is not None:
            num_files = check_type(num_files, int, "files_limit")
        max_workers = get_and_check(self._config, int, "caen_tasks", 0)
        task_timeout = get_and_check(self._config, int, "caen_timeout", 0)
        small_files_support = get_and_check(self._config, bool, "small_files", False)
        text_ui = get_and_check(self._config, bool, "text_ui", False)
        mem_usage_limit = 256  # MB
        # TODO get mem usage limit from config

        source_files = [
            f for f in self._get_limited_files_with_extension(num_files, ".csv")
        ]

        headers = self._find_csv_headers(source_files)
        total_cols = self._find_csv_cols(source_files)

        if small_files_support:
            results = self._convert_small_files(
                source_files,
                headers,
                total_cols,
                max_workers,
                text_ui,
                task_timeout,
                mem_usage_limit,
            )
        else:
            results = self._convert_normal_files(
                source_files, headers, total_cols, max_workers, text_ui
            )

        self._post_conversion_actions(results)

    def _find_csv_headers(self, source_files: List[Path]) -> List[str]:
        if len(source_files) == 0:
            headers = []
        else:
            source_file = get_first_source_file(source_files, END_NUMBER_PATTERN)

            with open(source_file, "r") as openfile:
                header_line = openfile.readline()
            headers = header_line.strip().split(DELIMITER)
        return headers

    def _find_csv_cols(self, source_files: List[Path]) -> int:
        if len(source_files) == 0:
            total_cols = 0
        else:
            source_file = get_first_source_file(source_files, END_NUMBER_PATTERN)

            with open(source_file, "r") as openfile:
                data_line = openfile.readline()
            data_sample = data_line.strip().split(DELIMITER)
            total_cols = len(data_sample)
        return total_cols

    def _convert_small_files(
        self,
        source_files: List[Path],
        headers: List[str],
        total_cols: int,
        max_workers: int,
        text_ui: int,
        task_timeout: int,
        mem_usage_limit: float,
    ) -> List[FolderResult]:
        folder_results: List[FolderResult] = []
        with tqdm(
            total=len(source_files),
            desc="CSV files",
            unit="file",
            bar_format=BAR_FORMAT,
            disable=not text_ui,
        ) as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                index = 0
                sample_files, remaining = split_list_by_count(source_files, max_workers)
                first_file_path = get_first_source_file(
                    source_files, END_NUMBER_PATTERN
                )
                sample_folder_results, dfs = self._convert_some_small_files(
                    ex, headers, total_cols, sample_files, task_timeout, pbar
                )
                folder_results.extend(sample_folder_results)

                df_dict_mem_usage = [
                    get_df_dict_mem_usage(df_dict) for _, df_dict in dfs
                ]
                total_mem_usage = sum(df_dict_mem_usage)
                avg_mem_usage = total_mem_usage / len(sample_files)
                batch_size = floor(mem_usage_limit / avg_mem_usage)
                files_remaining = batch_size - len(sample_files)

                if len(remaining) > 0 and files_remaining >= 1:
                    remaining_in_batch, remaining = split_list_by_count(
                        remaining, files_remaining
                    )
                    batch_results, batch_dfs = self._convert_some_small_files(
                        ex, headers, total_cols, remaining_in_batch, task_timeout, pbar
                    )
                    folder_results.extend(batch_results)
                    dfs.extend(batch_dfs)

                dfs.sort(key=lambda x: x[0])
                dfs = [df_dict for _, df_dict in dfs]
                psd_file_name = get_destination_file_name(first_file_path, index, "psd")
                signals_file_name = get_destination_file_name(
                    first_file_path, index, "signals"
                )
                # self._save_psd_data(dfs, psd_file_name)
                save_to_parquet(dfs, "psd", self._psd_dest / psd_file_name)
                # self._save_signals_data(dfs, signals_file_name)
                save_to_parquet(dfs, "signals", self._signals_dest / signals_file_name)

                while len(remaining) > 0:
                    index += 1
                    batch_files, remaining = split_list_by_count(remaining, batch_size)
                    batch_results, batch_dfs = self._convert_some_small_files(
                        ex, headers, total_cols, batch_files, task_timeout, pbar
                    )
                    folder_results.extend(batch_results)

                    batch_dfs.sort(key=lambda x: x[0])
                    batch_dfs = [df_dict for _, df_dict in dfs]

                    psd_file_name = get_destination_file_name(
                        first_file_path, index, "psd"
                    )
                    signals_file_name = get_destination_file_name(
                        first_file_path, index, "signals"
                    )
                    # self._save_psd_data(dfs, psd_file_name)
                    save_to_parquet(dfs, "psd", self._psd_dest / psd_file_name)
                    # self._save_signals_data(dfs, signals_file_name)
                    save_to_parquet(
                        dfs, "signals", self._signals_dest / signals_file_name
                    )

        return folder_results

    def _convert_normal_files(
        self,
        source_files: List[Path],
        headers: List[str],
        total_cols: int,
        text_ui: int,
        mem_usage_limit: float,
    ) -> List[FolderResult]:
        # TODO new design to make bigger merged output parquet files
        # wait for convert() changes (output dataframe)
        # merge output dataframes until size too big
        # then save to parquet
        results = []
        dfs: List[Dict[str, pd.DataFrame]] = []
        total_mem_usage = 0
        index = 0
        first_file_path = get_first_source_file(source_files, END_NUMBER_PATTERN)
        with tqdm(
            desc="CSV Files",
            unit="file",
            total=len(source_files),
            bar_format=BAR_FORMAT,
            disable=not text_ui,
        ) as progress_bar:
            for source_file in source_files:
                result, df_dict = convert_csv_file_to_df(
                    source_file,
                    # self._destination,
                    headers,
                    total_cols,
                    modin_pd.read_csv,
                    self._logfile_path,
                )
                progress_bar.update()
                results.append(result)
                if df_dict is not None:
                    dfs.append(df_dict)
                    mem_usage = get_df_dict_mem_usage(df_dict)
                    total_mem_usage += mem_usage
                    future_mem_usage = total_mem_usage + mem_usage
                else:
                    future_mem_usage = total_mem_usage
                # check if already over, or if one more would put us >10% over limit
                if (
                    total_mem_usage >= mem_usage_limit
                    or future_mem_usage >= 1.10 * mem_usage_limit
                ):
                    psd_file_name = get_destination_file_name(
                        first_file_path, index, "psd"
                    )
                    signals_file_name = get_destination_file_name(
                        first_file_path, index, "signals"
                    )
                    # self._save_psd_data(dfs, psd_file_name)
                    save_to_parquet(dfs, "psd", self._psd_dest / psd_file_name)
                    # self._save_signals_data(dfs, signals_file_name)
                    save_to_parquet(
                        dfs, "signals", self._signals_dest / signals_file_name
                    )
                    index += 1

        return results

    def _convert_some_small_files(
        self,
        ex: ThreadPoolExecutor,
        headers: List[str],
        total_cols: int,
        source_file_subset: List[Path],
        task_timeout: int,
        pbar,
    ) -> Tuple[List[FolderResult], List[Tuple[str, Dict[str, pd.DataFrame]]]]:
        folder_results: List[FolderResult] = []
        dfs: List[Tuple[str, Dict[str, pd.DataFrame]]] = []
        futures = [
            ex.submit(
                convert_csv_file_to_df,
                source_file,
                headers,
                total_cols,
                pd.read_csv,
                self._logfile_path,
            )
            for source_file in source_file_subset
        ]
        for future in as_completed(
            futures, timeout=task_timeout * len(source_file_subset)
        ):
            folder_result, df_dict = future.result()
            _, source_file_name = folder_result
            folder_results.append(folder_result)
            if df_dict is not None:
                dfs.append((source_file_name, df_dict))
            pbar.update(1)
        return folder_results, dfs

    # def _save_psd_data(self, dfs: List[Dict[str, pd.DataFrame]], file_name: str):
    #     # psd_dfs = [df_dict.get("psd") for df_dict in dfs]
    #     # psd_dfs = [df for df in psd_dfs if df is not None]
    #     # if len(psd_dfs) > 0:
    #     #     full_psd_df = pd.concat(psd_dfs, ignore_index=True)
    #     #     full_psd_df.to_parquet(self._destination / file_name)
    #     save_to_parquet(dfs, 'psd', self._destination / file_name)

    # def _save_signals_data(self, dfs: List[Dict[str, pd.DataFrame]], file_name: str):
    #     # signals_dfs = [df_dict.get("signals") for df_dict in dfs]
    #     # signals_dfs = [df for df in signals_dfs if df is not None]
    #     # if len(signals_dfs) > 0:
    #     #     full_signals_df = pd.concat(signals_dfs, ignore_index=True)
    #     #     full_signals_df.to_parquet(self._destination / file_name)
    #     save_to_parquet(dfs, 'signals', self._destination / file_name)
