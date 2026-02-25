from email.mime import base
from pathlib import Path
from tkinter import SINGLE
from typing import Iterable, Callable
import re

import polars as pl
import numpy as np
from data_converter.conversion.support.constants import (
    SINGLE_CHANNEL_DATA_PREFIX,
    DUAL_CHANNEL_DATA_PREFIX
)
from data_converter.conversion.support.csv_file_to_parquet_polars import DELIMITER, END_NUMBER_PATTERN, query_csv
from data_converter.conversion.support.abstract_folder_converter import AbstractFolderConverter
from utilities.utilities.configuration.configuration import Config
from data_converter.conversion.support.types import FolderResult


SAMPLES_COL_NAME = 'SAMPLES'
MAX_ROWS_PER_PART = 512000
PH_SCHEMA = {"PULSE_HEIGHT": pl.Float32}


class AbstractCSVtoParquetPolarsFolderConverter(AbstractFolderConverter):
    FILENAME_PATTERN = r"(.+)_(\d+)\.parquet"

    def __init__(
            self,
            source_folder: Path,
            destination_folders: Path | Iterable[Path],
            config: Config, 
            logfile_path: Path,
            logger_name: str = "csv_to_parquet_polars"
    ):
        super().__init__(
            source_folder, destination_folders, config, logfile_path, logger_name=logger_name
        )

    def _convert_files_with_prefix(
            self, target_file_prefix: str, destination: Path | Iterable[Path]
    ) -> list[FolderResult]:
        psd_dest_folder, signals_dest_folder = _get_split_data_destinations(destination)
        # Filters csv files for only the ones with matching prefix
        source_files = [
            f
            for f in self._get_limited_files_with_extension(None, ".csv")
            if re.match(f"^{target_file_prefix}.*", f.name)
        ]
        if len(source_files) == 0:
            return []
        first_file = [
            f
            for f in source_files
            if re.match(END_NUMBER_PATTERN, f.stem) is None
        ]
        if len(first_file) == 0:
            raise ValueError("Could not find csv file with headers")
        source_file = first_file[0]
        source_file_name = source_file.stem

        with open(source_file, "r") as openfile:
            header_line = openfile.readline()
            data_line = openfile.readline()
        headers = header_line.strip().split(DELIMITER)
        data_sample = data_line.strip().split(DELIMITER)
        total_cols = len(data_sample)
        psd_cols, signal_cols = _get_split_cols(headers, total_cols)
        all_cols = psd_cols + signal_cols

        lfs = [query_csv(filename, all_cols) for filename in source_files]
        all_lfs = pl.concat(lfs)
        
        if len(signal_cols) > 0:
            psd_dest_name, signals_dest_name = _get_split_parquet_names(source_file_name)
            psd_file_path_fn = self._get_part_filename_fn(Path(psd_dest_name))
            signals_file_path_fn = self._get_part_filename_fn(Path(signals_dest_name))

            psd_lf = all_lfs.select(psd_cols)
            signals_lf = all_lfs.select(signal_cols)

            # pulse_height_lf = (
            #     signals_lf
            #     .cast(pl.Float32)
            #     .map_batches(
            #         get_pulse_heights,
            #         projection_pushdown=False,
            #         schema=PH_SCHEMA
            #     )
            #     .cast(pl.String)
            # )
            # psd_with_ph_lf = pl.concat([psd_lf, pulse_height_lf], how="horizontal")
            psd_with_ph_lf = psd_lf

            psd_with_ph_lf.sink_parquet(
                pl.PartitionMaxSize(
                    psd_dest_folder,
                    file_path=psd_file_path_fn,
                    max_size=MAX_ROWS_PER_PART
                ),
                mkdir=True,
                lazy=True
            )
            signals_lf.sink_parquet(
                pl.PartitionMaxSize(
                    signals_dest_folder,
                    file_path=signals_file_path_fn,
                    max_size=MAX_ROWS_PER_PART
                ),
                mkdir=True,
                lazy=True
            )
            pl.collect_all([psd_with_ph_lf, signals_lf])
            rename_folders = [psd_dest_folder, signals_dest_folder]
        else:
            dest_name = f"caen_{source_file_name}.parquet"
            file_path_fn = self._get_part_filename_fn(Path(dest_name))
            all_lfs.sink_parquet(
                pl.PartitionMaxSize(
                    psd_dest_folder,
                    file_path=file_path_fn,
                    max_size=MAX_ROWS_PER_PART
                )
            )
            rename_folders = [psd_dest_folder]

        rename_pq_files(rename_folders, self.FILENAME_PATTERN)
        return [(True, source_file.name) for source_file in source_files]  # TODO determine if each file scan worked

    def _get_part_filename_fn(self, base_file_name: Path) -> Callable[[pl.BasePartitionContext], str]:
        # destination_stem = f"caen_{source_file_name}"
        # destination_name_pattern = destination_stem + "_{part}.parquet"
        stem = base_file_name.stem
        ext = base_file_name.suffix
        def partition_callback(ctx: pl.BasePartitionContext) -> str:
            return f"{stem}_{ctx.file_idx}{ext}"
        return partition_callback


class SingleChannelCSVPolarsConverter(AbstractCSVtoParquetPolarsFolderConverter):
    def __init__(
            self,
            source_folder: Path,
            destination: Path | Iterable[Path],
            config: Config,
            logfile_path: Path,
            logger_name: str = "csv_to_parquet_single_polars"):
        super().__init__(
            source_folder,
            destination,
            config,
            logfile_path,
            logger_name
        )

    def convert_folder(self):
        self._pre_conversion_actions()
        results = self._convert_files_with_prefix(
            SINGLE_CHANNEL_DATA_PREFIX, self._destination
        )
        self._post_conversion_actions(results)


class DualChannelCSVPolarsConverter(AbstractCSVtoParquetPolarsFolderConverter):
    def __init__(
            self,
            source_folder: Path,
            destination: Path | Iterable[Path],
            config: Config,
            logfile_path: Path,
            logger_name: str = "csv_to_parquet_polars_double"
    ):
        super().__init__(source_folder, destination, config, logfile_path, logger_name)

    def convert_folder(self):
        self._pre_conversion_actions()

        ch0_dest = self._get_path_with_channel_appended("ch0")
        self._make_dir_at_paths(ch0_dest)
        ch0_result = self._convert_files_with_prefix(
            f"{DUAL_CHANNEL_DATA_PREFIX}0", ch0_dest
        )

        ch1_dest = self._get_path_with_channel_appended("ch1")
        self._make_dir_at_paths(ch1_dest)
        ch1_results = self._convert_files_with_prefix(
            f"{DUAL_CHANNEL_DATA_PREFIX}1", ch1_dest
        )

        self._post_conversion_actions(ch0_result + ch1_results)

    def _get_path_with_channel_appended(self, channel_folder: str) -> Iterable[Path]:
        destinations = _get_split_data_destinations(self._destination)

        appended_paths = [Path(dest, channel_folder) for dest in destinations]
        return appended_paths

    def _make_dir_at_paths(self, destination: Iterable[Path]):
        for path in destination:
            path.mkdir(parents=True, exist_ok=True)


def _get_split_cols(
    headers: list[str],
    total_cols: int
) -> tuple[list[str], list[str]]:
    psd_cols = [col for col in headers if col != SAMPLES_COL_NAME]
    signal_cols = [str(n) for n
                   in range(total_cols - len(psd_cols))]
    return psd_cols, signal_cols


def _get_split_data_destinations(destination: Path | Iterable[Path]):
    if isinstance(destination, Path):
        # put everything in the same folder, even if signals exists
        psd_destination = destination
        signals_destination = destination
    else:
        psd_destination, *rest = destination
        try:
            signals_destination, *_ = rest
        except ValueError:
            signals_destination = psd_destination
    return psd_destination, signals_destination


def _get_split_parquet_names(source_file_name: str) -> tuple[str, str]:
    psd_dest_name = f"caen_psd_{source_file_name}.parquet"
    signals_dest_name = f"caen_samples_{source_file_name}.parquet"
    return psd_dest_name, signals_dest_name


def get_pulse_heights(
    raw_signals_df: pl.DataFrame,
    baseline_idx_range: int = 40,
    baseline_offset: float = 0,
    max_adc: int = 16367,
    use_max_adc: bool = False
) -> pl.DataFrame:
    
    offset = int(baseline_offset * max_adc)
    signals_np = raw_signals_df.to_numpy()

    if use_max_adc:
        baselines = max_adc
    else:
        baselines = signals_np[
            :, :baseline_idx_range
        ].mean(axis=1).reshape(-1, 1)

    signals_np = -signals_np + baselines + offset
    pulse_heights = np.max(signals_np, axis=1)

    corrected_signals = pl.DataFrame(
        pulse_heights,
        PH_SCHEMA
    )
    return corrected_signals


def rename_pq_files(folders: Iterable[Path], pattern: str):
    for folder in folders:
        if not folder.is_dir():
            continue
        pq_files = [file for file in folder.iterdir() if file.suffix == ".parquet"]
        file_count = len(pq_files)
        pad_length = len(str(file_count))
        for file in pq_files:
            match = re.match(pattern, file.name)
            if match is None:
                continue
            filename_start, raw_idx = match.groups()
            file_idx = raw_idx.zfill(pad_length)
            new_filepath = file.parent / f"{filename_start}_{file_idx}.parquet"
            file.rename(new_filepath)


# for subfolder in base_folder.iterdir():
#     if not subfolder.is_dir():
#         continue
#     file_count = sum((1 for filepath in subfolder.iterdir() if filepath.suffix == ".parquet"))
#     pad_length = len(str(file_count))
#     for filepath in subfolder.iterdir():
#         if filepath.suffix != ".parquet":
#             continue
#         # print(filepath.name)
#         match = re.match(pattern, filepath.name)
#         if match is None:
#             continue
#         filename_start, raw_idx = match.groups()
#         file_idx = raw_idx.zfill(pad_length)
#         new_filepath = filepath.parent / f"{filename_start}_{file_idx}.parquet"
#         filepath.rename(new_filepath)
#         # print(f"Renamed {filepath} to {new_filepath}")