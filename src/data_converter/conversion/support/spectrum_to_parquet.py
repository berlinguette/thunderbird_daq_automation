import logging
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer

logger = logging.getLogger('spectrum_to_parquet')
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)


def _find_matching_files(source_folder: Path, regex_string: str) -> List[Path]:
    expr = re.compile(regex_string)
    matching_files = [file for file in source_folder.iterdir()
                      if expr.match(file.name) and file.is_file()]
    return matching_files


def _try_convert_str_to_int(string: str) -> int:
    try:
        int_val = int(string)
        return int_val
    except ValueError:
        int_val = int(float(string))
        return int_val


def _split_spectrum_line(line: str) -> Tuple[float, int, float]:
    split_list = line.split(' ')
    index, count, energy, *_ = split_list
    # Energy spectrum channel can sometimes be a float
    # Might be due to calibration?
    # Either way, best to use most compatible conversion for all
    # since dataframe columns must have same type
    index = float(index)
    count = _try_convert_str_to_int(count)
    energy = float(energy)
    return index, count, energy


def _read_file_lines(file: Path) -> List[str]:
    with open(file, 'r') as readfile:
        lines = readfile.readlines()
    return lines


def _convert_energy_spectrum(files: List[Path], destination_folder: Path):
    energy_convert_timer = Timer(start_now=True)

    # do work
    for i, file in enumerate(files):
        lines = _read_file_lines(file)
        spectrum_data = [_split_spectrum_line(line) for line in lines[3:]]
        indexes = range(len(spectrum_data))
        spectrum_df = pd.DataFrame(spectrum_data,
                                   index=indexes,
                                   columns=['channel', 'count', 'bin_energy'])
        spectrum_df.to_parquet(
            destination_folder / f'energy_spectrum_{i}.parquet')

    exec_time = energy_convert_timer.stop_timer()
    formatted_time = energy_convert_timer.format_elapsed_time(
        exec_time, decimals=4)
    log_only_messenger.info(f"Converted {len(files)} energy spectrum files")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")


def _convert_psd_spectrum(files: List[Path], destination_folder: Path):
    psd_convert_timer = Timer(start_now=True)

    for i, file in enumerate(files):
        lines = _read_file_lines(file)

        spectrum_lines = [_try_convert_str_to_int(line) for line in lines]
        bins_count = len(spectrum_lines)
        indexes = list(range(bins_count))
        bin_width = 1/bins_count
        bin_low_bounds = [i*bin_width for i in range(bins_count)]
        spectrum_data = zip(spectrum_lines, bin_low_bounds)

        spectrum_df = pd.DataFrame(spectrum_data,
                                   index=indexes,
                                   columns=['count', 'bin_psd'])
        spectrum_df.to_parquet(
            destination_folder / f'psd_spectrum_{i}.parquet')

    exec_time = psd_convert_timer.stop_timer()
    formatted_time = psd_convert_timer.format_elapsed_time(
        exec_time, decimals=4)
    log_only_messenger.info(f"Converted {len(files)} PSD spectrum files")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")


def _convert_time_spectrum(
    files: List[Path],
    destination_folder: Path,
    min_time: float = 0.0,
    max_time: float = 1_000_000.0
):
    time_convert_timer = Timer(start_now=True)

    for i, file in enumerate(files):
        lines = _read_file_lines(file)

        spectrum_lines = [_try_convert_str_to_int(line) for line in lines]
        bins_count = len(spectrum_lines)
        indexes = list(range(bins_count))
        time_range = max_time - min_time
        bin_width = time_range/bins_count
        bin_low_bounds = [i*bin_width+min_time for i in range(bins_count)]
        spectrum_data = zip(spectrum_lines, bin_low_bounds)

        spectrum_df = pd.DataFrame(spectrum_data,
                                   index=indexes,
                                   columns=['count', 'bin_time'])
        spectrum_df.to_parquet(
            destination_folder / f'time_spectrum_{i}.parquet')

    exec_time = time_convert_timer.stop_timer()
    formatted_time = time_convert_timer.format_elapsed_time(
        exec_time, decimals=4)
    log_only_messenger.info(f"Converted {len(files)} time spectrum files")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")


def convert_spectra_to_parquet(
    source: Path, destination: Path, logfile_path: Path
):
    setup_logger(logger, logfile_path)
    log_only_messenger.debug(f"Starting spectrum conversion in {source.name}")
    timer = Timer(start_now=True)

    energy_spectrum_regex = r'.*Espectrum.*\.txt3$'
    psd_spectrum_regex = r'.*PSDspectrum.*\.txt$'
    time_spectrum_regex = r'.*Tspectrum.*\.txt$'
    energy_spectrum_files = _find_matching_files(source, energy_spectrum_regex)
    psd_spectrum_files = _find_matching_files(source, psd_spectrum_regex)
    time_spectrum_files = _find_matching_files(source, time_spectrum_regex)

    _convert_energy_spectrum(energy_spectrum_files, destination)
    _convert_psd_spectrum(psd_spectrum_files, destination)
    # TODO figure out min/max time spectrum values
    # appears to be 0-1,000,000 ns
    # should appear in settings.xml
    # may not be needed anyway if time spectrum not useful
    _convert_time_spectrum(time_spectrum_files, destination)

    exec_time = timer.stop_timer()
    formatted_time = timer.format_elapsed_time(exec_time, decimals=4)
    messenger.info(f"All spectrum files processed")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")
    cleanup_logger(logger)
