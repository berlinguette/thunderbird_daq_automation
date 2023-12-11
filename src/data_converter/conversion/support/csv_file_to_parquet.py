import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pandas import DataFrame
from tqdm import tqdm

from data_converter.conversion.support.types import FolderResult
from data_converter.utilities.logging import set_up_file_logging
from utilities.utilities.logging_helpers.setup_logger import cleanup_logger

SAMPLES_COL_NAME = "SAMPLES"
DELIMITER = ";"
END_NUMBER_PATTERN = r"^(.*_)(\d+)$"


def convert_csv_file_to_df(
    source_file: Path,
    # destination: Union[Path, Iterable[Path]],
    headers: List[str],
    total_cols: int,
    read_csv,
    logfile_path: Path,
) -> Tuple[FolderResult, Optional[Dict[str, DataFrame]]]:
    if not source_file.suffix.lower() == ".csv":
        return (False, f"File {source_file.name} is not a CSV file"), None

    new_logger, _ = set_up_file_logging(source_file, logfile_path)
    warnings.filterwarnings("ignore", "`to_parquet` is not currently supported")
    try:
        if SAMPLES_COL_NAME in headers:
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
                on_bad_lines="skip",
            )
            psd_df = df_raw[psd_cols]
            signals_df = df_raw[signal_cols]
            dfs = {"psd": psd_df, "signals": signals_df}
            worked = True
        else:
            data_df = read_csv(source_file, sep=DELIMITER, dtype=str)
            dfs = {"psd": data_df}
            worked = True
    except (MemoryError, IOError) as err:
        new_logger.exception(err)
        tqdm.write(
            f"Conversion failed for {source_file.name}. "
            + "See conversion.log for details"
        )
        dfs = None
        worked = False

    cleanup_logger(new_logger)
    return (worked, source_file.name), dfs


def _get_split_cols(headers: List[str], total_cols: int) -> Tuple[List[str], List[str]]:
    psd_cols = [col for col in headers if col != SAMPLES_COL_NAME]
    signal_cols = [str(n) for n in range(total_cols - len(psd_cols))]
    return psd_cols, signal_cols


def _has_header_line(source_file: Path) -> bool:
    return re.match(END_NUMBER_PATTERN, source_file.stem) is None
