import logging
import re
import tarfile
from collections import defaultdict
from pathlib import Path

import pandas as pd
from pymonad.either import Error, Result, _Error
from pymonad.tools import curry

from utilities.utilities.logging_helpers.setup_logger import (
    Messenger,
    cleanup_logger,
    setup_logger,
)
from utilities.utilities.timing import Timer

logger = logging.getLogger("reactor_data_to_parquet")
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)
archive_pattern = re.compile(r"(.+)_\d{8}-\d{9}_data")
data_file_pattern = re.compile(r"ID-\S+ (.+) (\d+)")


def convert_reactor_data_to_parquet(
    source: Path, destination: Path, logfile_path: Path
):
    setup_logger(logger, logfile_path)
    log_only_messenger.debug(f"Starting reactor data conversion in {source.name}")
    timer = Timer(start_now=True)

    get_reactor_data_path_with_source = get_reactor_data_path(source)  # type: ignore
    reactor_data_path: str | Path = (
        Result(source)  # Path
        .then(get_possible_reactor_data_paths)  # list[Path]
        .then(get_reactor_data_path_with_source)  # Path
        .either(lambda e: e, lambda x: x)  # type: ignore
    )
    if isinstance(reactor_data_path, str):
        messenger.info(reactor_data_path)
        return
    log_only_messenger.debug(f"Found reactor data archive at {reactor_data_path}")
    experiment_id: str = archive_pattern.match(reactor_data_path.name).group(1)  # type: ignore

    reactor_dfs: dict[str, list[pd.DataFrame]] = defaultdict(list)
    with tarfile.open(reactor_data_path, "r:*") as reactor_tar:
        get_df_match_from_reactor_tar = get_df_with_match(reactor_tar)  # type: ignore
        for filename in reactor_tar.getnames():
            csv_result: str | tuple[re.Match, pd.DataFrame] = (  # type: ignore
                Result(filename)  # str
                .then(Path)  # Path
                .then(only_csv_paths)  # Path
                .then(get_name_match)  # Match
                .then(get_df_match_from_reactor_tar)  # (Match, Dataframe)
                .either(lambda e: e, lambda x: x)  # type: ignore
            )
            if isinstance(csv_result, str):
                print(csv_result)
                continue
            match, df = csv_result
            reactor_dfs[match.group(1)].append(df)
    for device_param, dfs in reactor_dfs.items():
        merged_df = pd.concat(dfs).sort_values("Timestamp", ignore_index=True)
        parquet_path = destination / f"{experiment_id}_{device_param}_data.parquet"
        merged_df.to_parquet(parquet_path)

    exec_time = timer.stop_timer()
    formatted_time = timer.format_elapsed_time(exec_time, decimals=4)
    messenger.info("Reactor data processed")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")
    cleanup_logger(logger)


def get_possible_reactor_data_paths(source: Path) -> list[Path]:
    return [
        file_path
        for file_path in source.iterdir()
        if _is_reactor_data_archive(file_path)
    ]


@curry(2)
def get_reactor_data_path(source: Path, matches: list[Path]) -> Path | _Error:
    return (
        matches[0]
        if len(matches) >= 1
        else Error(f"No reactor data archive files found in {source}")
    )


def _is_reactor_data_archive(file_path: Path) -> bool:
    is_tar = "tar" in file_path.suffixes
    is_gzip = "gz" in file_path.suffixes
    name_pattern_match = archive_pattern.match(file_path.name)
    return file_path.is_file() and is_tar and is_gzip and name_pattern_match is not None


def only_csv_paths(path: Path) -> Path | _Error:
    return path if path.suffix.lower() == ".csv" else Error("Not a CSV file")


def get_name_match(path: Path) -> re.Match | _Error:
    name_match = data_file_pattern.match(path.name)
    if name_match is None:
        return Error("No match")
    return name_match


@curry(2)
def get_df_with_match(
    tarfile: tarfile.TarFile, match: re.Match
) -> tuple[re.Match, pd.DataFrame] | _Error:
    result = get_df_from_tarfile(tarfile, match.group(0))
    if isinstance(result, _Error):
        return result
    return match, result


def get_df_from_tarfile(
    tarfile: tarfile.TarFile, filename: str
) -> pd.DataFrame | _Error:
    x = tarfile.extractfile(filename)
    if x is None:
        return Error(f"Could not extract {filename} from archive")
    try:
        return pd.read_csv(x, encoding="windows-1252")
    except Exception as err:
        return Error(str(err))
