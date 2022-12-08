import logging
import re
import warnings
from itertools import islice, repeat
from pathlib import Path
from typing import Iterable
from tqdm import tqdm

import modin.pandas as modin_pd
import pandas as pd

from utilities.utilities.check_type import check_type, get_and_check
from utilities.utilities.configuration.configuration import Config
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer
from data_converter.utilities.constants import BAR_FORMAT
from tqdm.contrib.concurrent import thread_map

logger = logging.getLogger('csv_to_parquet')
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)

DELIMITER = ';'
SAMPLES_COL_NAME = 'SAMPLES'
END_NUMBER_PATTERN = r'(.*_)(\d+)'


def _get_limited_files_with_extension(
    folder_path: Path,
    limit: None | int,
    extension: str
) -> Iterable[Path]:
    ext_files_generator = (file for file in folder_path.iterdir()
                           if file.is_file() and file.suffix.lower() == extension)
    if limit is None or limit == 0:
        files = ext_files_generator
    else:
        files = islice(ext_files_generator, limit)
    return files


def _set_up_file_logging(
    source_file: Path,
    logfile_path: Path
) -> tuple[logging.Logger, Messenger]:
    source_name = source_file.name
    new_logger = logging.getLogger(f'proc-{source_name}')
    # source_file parent is RAW folder, so root is one more level up
    setup_logger(new_logger, logfile_path)
    new_messenger = Messenger(new_logger, on_screen=False)
    new_messenger.debug(f"Converting {source_name}...")
    return new_logger, new_messenger


def _get_destination_file_name(source_file: Path) -> str:
    file_number_length = 5  # i.e. run_00000, supports 100,000 files
    pattern = r'.+_\d{' + re.escape(str(file_number_length)) + r'}'
    source_file_name = source_file.stem
    if not re.match(pattern, source_file_name):
        match = re.match(END_NUMBER_PATTERN, source_file_name)
        if match:
            start, number = match.group(1, 2)
            fixed_number = str(number).zfill(file_number_length)
            source_file_name = str(start) + fixed_number
        else:
            starting_file_number = '0'.zfill(file_number_length)
            # source_file_name = source_file_name + '_00000'
            source_file_name = f"{source_file_name}_{starting_file_number}"
    return source_file_name


def _get_split_data_destinations(destination: Path | tuple[Path, Path]):
    if isinstance(destination, Path):
        # put everything in the same folder, even if signals exists
        psd_destination = destination
        signals_destination = destination
    else:
        # destination tuple = psd subfolder, signals subfolder
        # so if signals column exists, split and save appropriately
        # otherwise, just use psd folder
        psd_destination, signals_destination = destination
    return psd_destination, signals_destination


def _get_split_parquet_names(source_file_name: str) -> tuple[str, str]:
    psd_dest_name = f"caen_psd_{source_file_name}.parquet"
    signals_dest_name = f"caen_samples_{source_file_name}.parquet"
    return psd_dest_name, signals_dest_name


def _get_split_cols(
    headers: list[str],
    total_cols: int
) -> tuple[list[str], list[str]]:
    psd_cols = [col for col in headers if col != SAMPLES_COL_NAME]
    signal_cols = [str(n) for n
                   in range(total_cols - len(psd_cols))]
    return psd_cols, signal_cols


def _has_header_line(source_file: Path) -> bool:
    return re.match(END_NUMBER_PATTERN, source_file.stem) is None

def _do_csv_conversion(source_file: Path, destination: Path | tuple[Path, Path], headers: list[str], total_cols: int, read_csv, logfile_path: Path):
    new_logger, _ = _set_up_file_logging(source_file, logfile_path)
    source_file_name = _get_destination_file_name(source_file)
    psd_destination, signals_destination = _get_split_data_destinations(
        destination)
    warnings.filterwarnings('ignore',
                            '`to_parquet` is not currently supported')
    try:
        if SAMPLES_COL_NAME in headers:
            psd_dest_name, signals_dest_name = _get_split_parquet_names(
                source_file_name)
            psd_cols, signal_cols = _get_split_cols(headers, total_cols)
            all_cols = psd_cols + signal_cols
            header = 0 if _has_header_line(source_file) else None
            df_raw = read_csv(
                source_file,
                sep=DELIMITER,
                header=header,
                names=all_cols,
                dtype=str,
                # TODO warn on bad lines, catch warnings, log
                on_bad_lines='skip'
            )
            psd_df = df_raw[psd_cols]
            signals_df = df_raw[signal_cols]
            psd_df.to_parquet(psd_destination / psd_dest_name)
            signals_df.to_parquet(signals_destination / signals_dest_name)
        else:
            destination_name = f"caen_{source_file_name}.parquet"
            data_df = read_csv(source_file, sep=DELIMITER, dtype=str)
            data_df.to_parquet(psd_destination / destination_name)
    except (MemoryError, IOError) as err:
            new_logger.exception(err)
            tqdm.write(
                f"Conversion failed for {source_file.name}. " +
                "See conversion.log for details")
            return False, source_file.name
    return True, source_file.name


def convert_csv_folder_to_parquet(
    source: Path, destination: Path | tuple[Path, Path], config: Config, logfile_path: Path
):
    setup_logger(logger, logfile_path)
    timer = Timer(start_now=True)

    num_files = config.get('files_limit')
    if num_files is not None:
        num_files = check_type(num_files, int, 'files_limit')
    csv_workers = get_and_check(config, int, 'csv_tasks', 0)
    csv_timeout = get_and_check(config, int, 'csv_timeout', 0)
    large_files_support = get_and_check(config, bool, 'large_files', False)

    file_paths = [
        f for f in _get_limited_files_with_extension(
            source, num_files, '.csv'
        )
    ]

    csv_timeout = csv_timeout * len(file_paths)
    if csv_timeout == 0:
        csv_timeout = None

    if len(file_paths) == 0:
        headers = []
        total_cols = 0
    else:
        first_file = [f for f
                      in _get_limited_files_with_extension(source, None, '.csv')
                      if re.match(r'.*_\d+', f.stem) is None]
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
            total=len(file_paths),
            bar_format=BAR_FORMAT
        ) as progress_bar:
            for file_path in file_paths:
                result = _do_csv_conversion(
                    file_path, 
                    destination, 
                    headers, 
                    total_cols, 
                    modin_pd.read_csv, 
                    logfile_path
                )
                progress_bar.update()
                results.append(result)
    else:
        results = thread_map(
            _do_csv_conversion,
            file_paths,
            repeat(destination),
            repeat(headers),
            repeat(total_cols),
            repeat(pd.read_csv),
            repeat(logfile_path),
            timeout=csv_timeout,
            max_workers=csv_workers,
            desc='CSV files',
            unit='file',
            total=len(file_paths),
            bar_format=BAR_FORMAT
        )

    exec_time = timer.stop_timer()
    results = list(results)
    good_results = [filename for worked, filename in results if worked]
    bad_results = [filename for worked, filename in results if not worked]
    messenger.info(f"Processed {len(results)} files")
    messenger.info(f"{len(good_results)} completely successful files")
    messenger.info(f"{len(bad_results)} files with conversion issues. " +
                   "See logs for more information.")
    log_only_messenger.debug("Failing files:")
    for result in bad_results:
        log_only_messenger.debug(f"     {result}")
    log_only_messenger.debug(
        f"Elapsed time: {timer.format_elapsed_time(exec_time, decimals=4)}")
    cleanup_logger(logger)
