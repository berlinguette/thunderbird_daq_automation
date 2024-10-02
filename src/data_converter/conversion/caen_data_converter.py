import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Protocol, TypeVar

import tomli_w

from data_converter.conversion.abstract_data_converter import AbstractDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.folder_converter_factory import (
    FolderConverterFactory,
)
from data_converter.conversion.support.spectrum_to_parquet import (
    convert_spectra_to_parquet,
)
from data_converter.utilities.input_with_timeout import input_with_timeout
from data_converter.conversion.support.reactor_data_to_parquet import (
    convert_reactor_data_to_parquet,
)
from utilities.utilities.check_type import get_and_check

KEY_RAW_DATA = "raw_data_folder"
KEY_FILTERED_DATA = "filtered_data_folder"
KEY_UNFILTERED_DATA = "unfiltered_data_folder"
KEY_DATASET_ROOT = "dataset_root"
KEY_DATASET_RAW = "dataset_raw_data"
KEY_DATASET_RAW_CSV = "dataset_raw_data_csv"
KEY_DATASET_RAW_PARQUET = "dataset_raw_data_parquet"
KEY_DATASET_PROCESSED = "dataset_processed_data"
KEY_DATASET_REACTOR = "dataset_reactor_data"
KEY_DATASET_FILTERED = "dataset_processed_filtered"
KEY_DATASET_FILTERED_PSD = "dataset_filtered_psd"
KEY_DATASET_FILTERED_SIGNALS = "dataset_filtered_signals"
KEY_DATASET_FILTERED_SPECTRA = "dataset_filtered_spectra"
KEY_DATASET_UNFILTERED = "dataset_processed_unfiltered"
KEY_DATASET_UNFILTERED_PSD = "dataset_unfiltered_psd"
KEY_DATASET_UNFILTERED_SIGNALS = "dataset_unfiltered_signals"
KEY_DATASET_UNFILTERED_SPECTRA = "dataset_unfiltered_spectra"

C = TypeVar("C")


class Comparable(Protocol):
    def __eq__(self, __other: Any) -> bool: ...

    def __lt__(self: C, __other: C) -> bool: ...

    def __gt__(self: C, __other: C) -> bool: ...

    def __le__(self: C, __other: C) -> bool: ...

    def __ge__(self: C, __other: C) -> bool: ...


class CaenDataConverter(AbstractDataConverter):
    def convert(self) -> bool:
        try:
            paths_dict = self._determine_paths()
            self._initial_messages()
            self._prepare_dataset_destinations(paths_dict)
            self._conversion_process(paths_dict)
            self._finish_conversion()
            return True
        except Exception as err:
            self._logger.exception(err)
            return False

    def _determine_paths(self) -> Dict[str, Path]:
        raw_data_folder = self._experiment_source.joinpath(
            constants.CAEN_RAW_FOLDER_NAME
        )
        filtered_data_folder = self._experiment_source.joinpath(
            constants.CAEN_FILTERED_FOLDER_NAME
        )
        unfiltered_data_folder = self._experiment_source.joinpath(
            constants.CAEN_UNFILTERED_FOLDER_NAME
        )
        # dataset_root_folder = (self._destination /
        #                        self._experiment_root.name)
        dataset_raw_folder = self._destination.joinpath(
            constants.DATASET_RAW_DATA_FOLDER_NAME
        )
        dataset_raw_original_folder = dataset_raw_folder.joinpath(
            constants.CAEN_RAW_FOLDER_NAME
        )
        dataset_raw_parquet_folder = dataset_raw_folder.joinpath(
            constants.DATASET_PARQUET_FOLDER_NAME
        )
        dataset_processed_folder = self._destination.joinpath(
            constants.DATASET_PROCESSED_DATA_FOLDER_NAME
        )
        dataset_reactor_folder = dataset_processed_folder.joinpath(
            constants.DATASET_REACTOR_DATA_FOLDER_NAME
        )
        dataset_filtered_folder = dataset_processed_folder.joinpath(
            constants.CAEN_PROCESSED_FILTERED_FOLDER_NAME
        )
        dataset_filtered_psd_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_PSD_FOLDER_NAME
        )
        dataset_filtered_signals_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_SIGNALS_FOLDER_NAME
        )
        dataset_filtered_spectra_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_SPECTRA_FOLDER_NAME
        )
        dataset_unfiltered_folder = dataset_processed_folder.joinpath(
            constants.CAEN_PROCESSED_UNFILTERED_FOLDER_NAME
        )
        dataset_unfiltered_psd_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_PSD_FOLDER_NAME
        )
        dataset_unfiltered_signals_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_SIGNALS_FOLDER_NAME
        )
        dataset_unfiltered_spectra_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_SPECTRA_FOLDER_NAME
        )
        return {
            KEY_RAW_DATA: raw_data_folder,
            KEY_FILTERED_DATA: filtered_data_folder,
            KEY_UNFILTERED_DATA: unfiltered_data_folder,
            KEY_DATASET_ROOT: self._destination,
            KEY_DATASET_RAW: dataset_raw_folder,
            KEY_DATASET_RAW_CSV: dataset_raw_original_folder,
            KEY_DATASET_RAW_PARQUET: dataset_raw_parquet_folder,
            KEY_DATASET_PROCESSED: dataset_processed_folder,
            KEY_DATASET_REACTOR: dataset_reactor_folder,
            KEY_DATASET_FILTERED: dataset_filtered_folder,
            KEY_DATASET_FILTERED_PSD: dataset_filtered_psd_folder,
            KEY_DATASET_FILTERED_SIGNALS: dataset_filtered_signals_folder,
            KEY_DATASET_FILTERED_SPECTRA: dataset_filtered_spectra_folder,
            KEY_DATASET_UNFILTERED: dataset_unfiltered_folder,
            KEY_DATASET_UNFILTERED_PSD: dataset_unfiltered_psd_folder,
            KEY_DATASET_UNFILTERED_SIGNALS: dataset_unfiltered_signals_folder,
            KEY_DATASET_UNFILTERED_SPECTRA: dataset_unfiltered_spectra_folder,
        }

    def _prepare_dataset_destinations(self, paths: Dict[str, Path]):
        dataset_raw_folder = paths[KEY_DATASET_RAW]
        dataset_raw_original_folder = paths[KEY_DATASET_RAW_CSV]
        dataset_processed_folder = paths[KEY_DATASET_PROCESSED]
        dataset_unfiltered_folder = paths[KEY_DATASET_UNFILTERED]
        dataset_unfiltered_folder_psd = paths[KEY_DATASET_UNFILTERED_PSD]
        dataset_unfiltered_signals_folder = paths[KEY_DATASET_UNFILTERED_SIGNALS]
        dataset_unfiltered_spectra_folder = paths[KEY_DATASET_UNFILTERED_SPECTRA]
        dataset_unfiltered_reactor_folder = paths[KEY_DATASET_REACTOR]

        self._messenger.info("Preparing destination folders")
        self._prepare_destinations([dataset_raw_folder, dataset_raw_original_folder])
        self._messenger.debug(" - Raw CSV destination done")
        self._messenger.debug(" - Raw Parquet destination done")
        self._prepare_destinations(
            [
                dataset_processed_folder,
                dataset_unfiltered_folder,
                dataset_unfiltered_folder_psd,
                dataset_unfiltered_signals_folder,
                dataset_unfiltered_spectra_folder,
                dataset_unfiltered_reactor_folder,
            ]
        )
        self._messenger.debug(" - Processed data destination done")

        self._screen_only_messenger.info("")

    def _conversion_process(self, paths: Dict[str, Path]):
        raw_data_folder = paths[KEY_RAW_DATA]
        dataset_root_folder = paths[KEY_DATASET_ROOT]
        dataset_raw_csv_folder = paths[KEY_DATASET_RAW_CSV]
        dataset_processed_folder = paths[KEY_DATASET_PROCESSED]
        dataset_reactor_folder = paths[KEY_DATASET_REACTOR]
        unfiltered_data_folder = paths[KEY_UNFILTERED_DATA]
        dataset_unfiltered_psd_folder = paths[KEY_DATASET_UNFILTERED_PSD]
        dataset_unfiltered_signals_folder = paths[KEY_DATASET_UNFILTERED_SIGNALS]
        dataset_unfiltered_spectra_folder = paths[KEY_DATASET_UNFILTERED_SPECTRA]

        self._messenger.info("Generating metadata file")
        self._generate_metadata_file(paths)
        self._screen_only_messenger.info("")

        self._messenger.info("Converting unfiltered data to Parquet")
        folder_converter = FolderConverterFactory().make_folder_converter(
            unfiltered_data_folder,
            [dataset_unfiltered_psd_folder, dataset_unfiltered_signals_folder],
            self._config,
            self._logfile_path,
        )
        folder_converter.convert_folder()
        convert_spectra_to_parquet(
            unfiltered_data_folder,
            dataset_unfiltered_spectra_folder,
            self._logfile_path,
        )
        self._screen_only_messenger.info("")

        self._messenger.info("Converting reactor data to Parquet")
        convert_reactor_data_to_parquet(
            self._experiment_source, dataset_reactor_folder, self._logfile_path
        )
        self._screen_only_messenger.info("")

        self._messenger.info("Moving raw data files to destination")
        move_files = get_and_check(self._config, bool, "move_files", False)
        for file in raw_data_folder.iterdir():
            if file.is_file() and file.suffix.lower() in [".csv", ".bin"]:
                # file.rename(dataset_raw_csv_folder / file.name)
                status_msg = self._handle_raw_file(
                    file, dataset_raw_csv_folder / file.name, move_file=move_files
                )
                self._messenger.info(status_msg)
        for file in self._experiment_source.iterdir():
            if file.is_file() and file.name.lower() == "settings.xml":
                # file.rename(dataset_root_folder / file.name)
                status_msg = self._handle_raw_file(
                    file, dataset_root_folder / file.name, move_file=move_files
                )
                self._messenger.info(status_msg)
        self._screen_only_messenger.info("")

    def _generate_metadata_file(
        self, paths: Dict[str, Path]
    ):  # TODO use config to get and use start time (if provided via CLI)
        dataset_root_folder = paths[KEY_DATASET_ROOT]
        run_info_path = self._experiment_source / "run.info"
        metadata_dest_path = dataset_root_folder.joinpath(
            constants.DATASET_METADATA_FILE_TOML
        )

        try:
            with open(run_info_path, "r") as infofile:
                info_lines = infofile.readlines()
            from_run_info = True
        except FileNotFoundError:
            info_lines = self._get_info_lines()
            from_run_info = False

        if from_run_info and len(info_lines) < 2:
            print("run.info did not have enough data to use")
            info_lines = self._get_info_lines()
            from_run_info = False

        id_pattern = re.compile(r"^id=(.*)$")
        id_matches = [id_pattern.match(line) for line in info_lines]
        id_matches = [match for match in id_matches if match is not None]
        if len(id_matches) == 0:
            raise ValueError(f"Id could not be read from file {run_info_path}")
        id = id_matches[0].group(1)

        start_time_pattern = re.compile(r"^time.start=(.*)$")
        time_matches = [start_time_pattern.match(line) for line in info_lines]
        time_matches = [match for match in time_matches if match is not None]
        if len(time_matches) == 0:
            raise ValueError(f"Start time could not be read from file {run_info_path}")
        time_start = time_matches[0].group(1)
        time_start = time_start.replace("/", "-")
        time_start = f"{time_start[:-2]}:{time_start[-2:]}"

        start_datetime = datetime.fromisoformat(time_start)
        start_date_stamp = start_datetime.date().strftime("%Y%m%d")
        metadata = {
            "exp_id": f"{start_date_stamp}_{id}",
            "desc": "<Add Description>",
            "exp_start": start_datetime,
            "from_run_info_file": from_run_info,
        }

        with open(metadata_dest_path, "wb") as savefile:
            tomli_w.dump(metadata, savefile)

    def _input_caen_start_time(self) -> datetime:
        now = datetime.now()
        valid_date = False
        while not valid_date:
            print("try start input")
            year = self._get_valid_value(
                f"Enter year (default = {now.year})> ",
                int,
                default=now.year,
                timeout=20,
            )
            month = self._get_valid_value(
                f"Enter month (1-12, default = {now.month})> ",
                int,
                default=now.month,
                min=1,
                max=12,
            )
            day = self._get_valid_value(
                f"Enter day (1-31, default = {now.day})> ",
                int,
                default=now.day,
                min=1,
                max=31,
            )
            try:
                datetime(year, month, day)
                valid_date = True
            except ValueError:
                self._messenger.info("Invalid date, please try again")
        hour = self._get_valid_value(
            f"Enter hour (0-23, default = {now.hour})> ",
            int,
            default=now.hour,
            min=0,
            max=23,
        )
        minute = self._get_valid_value(
            f"Enter minute (0-59, default = {now.minute})> ",
            int,
            default=now.minute,
            min=0,
            max=59,
        )
        return datetime(year, month, day, hour, minute)

    CT = TypeVar("CT", bound=Comparable)

    def _get_valid_value(
        self,
        prompt: str,
        converter: Callable[[str], CT],
        default: CT | None = None,
        min: CT | None = None,
        max: CT | None = None,
        timeout: int | None = None,
    ) -> CT:
        if default is not None:
            if min is not None and default < min:
                raise ValueError("Default value must not be less than minimum value")
            if max is not None and default > max:
                raise ValueError("Default value must not be more than maximum value")

        while True:
            try:
                in_str = input_with_timeout(prompt, timeout=timeout)
            except ValueError as err:
                print()
                print(f"Timeout: {err}")
                raise err
            try:
                in_val = converter(in_str)
            except ValueError:
                if default is not None:
                    return default
                else:
                    self._messenger.info("Input value was not valid, please try again")
                    continue
            min_valid = min is None or (min is not None and in_val >= min)
            max_valid = max is None or (max is not None and in_val <= max)
            if min_valid:
                if max_valid:
                    return in_val
                else:
                    self._messenger.info(
                        "Input value was higher than maximum allowed, please try again"
                    )
            else:
                self._messenger.info(
                    "Input value was lower that minimum allowed, please try again"
                )

    def _get_info_lines(self) -> list[str]:
        self._messenger.info("Could not find run.info file")
        if self._experiment_source.is_dir():
            id = self._experiment_source.name
            self._messenger.info("Experiment ID found from folder")
        else:
            id = input("Please enter the ID of this experiment")
        if "ID-" not in id and "TB-" not in id:
            id_format = input(
                """What kind of ID format are you using?
1: Old format (ID-XXX)
2: New format (TB-XXX) (default)
Enter a value or press Enter for default
"""
            )
            if id_format == "1":
                id_prefix = "ID-"
            elif id_format == "2":
                id_prefix = "TB-"
            else:
                print("Using default value")
                id_prefix = "TB-"
            id = f"{id_prefix}{id}"
        self._messenger.info(f"Using experiment ID {id}")
        id_line = f"id={id}"

        self._messenger.info(str(self._config.get("start_time", None)))
        try:
            start_time_arg = get_and_check(self._config, str, "start_time")
        except ValueError:
            start_time_arg = None
        self._messenger.info(f"Start time arg: {start_time_arg}")
        if start_time_arg is not None:
            try:
                start_time = datetime.strptime(start_time_arg, "%Y/%m/%d-%H:%M")
            except ValueError:
                self._messenger.info(
                    "Please enter the start date and time of neutron detection:"
                )
                start_time = self._input_caen_start_time()
        else:
            self._messenger.info(
                "Please enter the start date and time of neutron detection:"
            )
            start_time = self._input_caen_start_time()

        now = datetime.now(timezone.utc).astimezone()
        now_tz = now.tzinfo
        start_time = start_time.astimezone(now_tz)
        start_time_str = start_time.strftime("%Y/%m/%d %H:%M:%S.%f%z")
        start_time_line = f"time.start={start_time_str}"

        return [id_line, start_time_line]
