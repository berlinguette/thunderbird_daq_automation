import re
import warnings
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

from tqdm import tqdm

from data_converter.conversion.support.types import FolderResult
from data_converter.utilities.logging import set_up_file_logging
from utilities.utilities.logging_helpers.setup_logger import cleanup_logger

SAMPLES_COL_NAME = 'SAMPLES'
DELIMITER = ';'
END_NUMBER_PATTERN = r'^(.*_)(\d+)$'


def convert_csv_file_to_parquet(
    source_file: Path,
    destination: Union[Path, Iterable[Path]],
    headers: List[str],
    total_cols: int,
    read_csv,
    logfile_path: Path
) -> FolderResult:
    if not source_file.suffix.lower() == ".csv":
        return False, f"File {source_file.name} is not a CSV file"

    new_logger, _ = set_up_file_logging(source_file, logfile_path)
    source_file_name = _get_destination_file_name(source_file)
    psd_destination, signals_destination = _get_split_data_destinations(
        destination)
    warnings.filterwarnings('ignore',
                            '`to_parquet` is not currently supported')
    print(f"Converting {source_file_name}")
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
            print(f"Saved as {psd_dest_name} and {signals_dest_name}")
            worked = True
        else:
            destination_name = f"caen_{source_file_name}.parquet"
            data_df = read_csv(source_file, sep=DELIMITER, dtype=str)
            data_df.to_parquet(psd_destination / destination_name)
            print(f"Saved as {destination_name}")
            worked = True
    except (MemoryError, IOError) as err:
        print(f"Error: {err}")
        new_logger.exception(err)
        tqdm.write(
            f"Conversion failed for {source_file.name}. " +
            "See conversion.log for details")
        worked = False

    cleanup_logger(new_logger)
    return worked, source_file.name


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


def _get_split_data_destinations(destination: Union[Path, Iterable[Path]]):
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


def _get_split_parquet_names(source_file_name: str) -> Tuple[str, str]:
    psd_dest_name = f"caen_psd_{source_file_name}.parquet"
    signals_dest_name = f"caen_samples_{source_file_name}.parquet"
    return psd_dest_name, signals_dest_name


def _get_split_cols(
    headers: List[str],
    total_cols: int
) -> Tuple[List[str], List[str]]:
    psd_cols = [col for col in headers if col != SAMPLES_COL_NAME]
    signal_cols = [str(n) for n
                   in range(total_cols - len(psd_cols))]
    return psd_cols, signal_cols


def _has_header_line(source_file: Path) -> bool:
    return re.match(END_NUMBER_PATTERN, source_file.stem) is None
