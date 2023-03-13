import re
from pathlib import Path
from typing import Optional, Tuple, Union

from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.caen_data_converter import CaenDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.enums import ExperimentType
from data_converter.conversion.wendi_data_converter import WendiDataConverter
from utilities.utilities.configuration.configuration import Config, ConfigSetup

CAEN_RAW_DATA_FOLDERS = [
    constants.CAEN_FILTERED_FOLDER_NAME,
    constants.CAEN_OFFLINE_FOLDER_NAME,
    constants.CAEN_RAW_FOLDER_NAME,
    constants.CAEN_SCREENSHOTS_FOLDER_NAME,
    constants.CAEN_UNFILTERED_FOLDER_NAME
]


class DataConverterFactory:
    def make_converter(
        self,
        exp_folder: Path,
        config: Config,
        config_setup: ConfigSetup,
        destination: Path
    ) -> Tuple[AbstractDataConverter, ExperimentType]:
        found_schema = self._determine_data_schema(exp_folder)
        if found_schema is None:
            raise ValueError(
                f"Experiment root could not be found for folder {exp_folder}")
        exp_type, exp_root = found_schema
        if exp_type == ExperimentType.CAEN:
            converter = CaenDataConverter(
                exp_root, config, config_setup, destination)
        elif exp_type == ExperimentType.WENDI:
            converter = WendiDataConverter(
                exp_root, config, config_setup, destination)
        else:
            raise ValueError(f"Invalid experiment type {exp_type}")
        return converter, exp_type

    def _find_caen_root(
        self, source_path: Path, found_subfolder: Optional[str] = None
    ) -> Optional[Path]:
        root_path = None
        if not source_path.is_dir():
            return self._find_caen_root(source_path.parent)
        if source_path.name in CAEN_RAW_DATA_FOLDERS:
            found_subfolder = source_path.name
            if source_path.name == constants.CAEN_RAW_FOLDER_NAME:
                data_file_pattern = re.compile(
                    r'SDataR_.*\.[CSV|BIN]$)', flags=re.IGNORECASE)
                if not self._does_matching_file_exist(
                        source_path, data_file_pattern):
                    return None
            elif source_path.name == constants.CAEN_UNFILTERED_FOLDER_NAME:
                data_file_pattern = re.compile(
                    r'SData_.*\.[CSV|BIN]$', flags=re.IGNORECASE)
                if not self._does_matching_file_exist(
                        source_path, data_file_pattern):
                    return None
            root_path = self._find_caen_root(
                source_path.parent, found_subfolder=found_subfolder)
        else:
            def check_caen_subfolder(folder_name: str) -> bool:
                return (
                    found_subfolder == folder_name or
                    (source_path / folder_name).exists())

            checks = [
                (source_path / constants.CAEN_RUN_INFO).exists(),
                (source_path / constants.CAEN_SETTINGS_XML).exists(),
                check_caen_subfolder(constants.CAEN_FILTERED_FOLDER_NAME),
                # check_caen_subfolder(constants.CAEN_OFFLINE_FOLDER_NAME),
                check_caen_subfolder(constants.CAEN_RAW_FOLDER_NAME),
                # check_caen_subfolder(constants.CAEN_SCREENSHOTS_FOLDER_NAME),
                check_caen_subfolder(constants.CAEN_UNFILTERED_FOLDER_NAME)
            ]
            if all(checks):
                root_path = source_path
        return root_path

    def _is_wendi_logfile(self, source_path: Path) -> bool:
        if source_path.is_file() and source_path.suffix.lower() == '.log':
            with open(source_path, 'r', encoding='cp1252', errors='replace') as source_file:
                line = source_file.readline()
            model_number = line[:5]
            return model_number == "FH40G"
        return False

    def _determine_data_schema(
        self,
        source_path: Path
    ) -> Optional[Tuple[ExperimentType, Path]]:
        if self._is_wendi_logfile(source_path):
            return ExperimentType.WENDI, source_path

        root_path = self._find_caen_root(source_path)
        if root_path is not None:
            return ExperimentType.CAEN, root_path

        return None

    @staticmethod
    def _does_matching_file_exist(folder_path: Path, pattern: re.Pattern) -> bool:
        return any((
            pattern.fullmatch(file.name) for file in folder_path.iterdir()
        ))

    def _are_psdata_files_here(self, folder_path: Path) -> bool:
        return self._does_matching_file_exist(
            folder_path,
            re.compile(r".*\.psdata$", flags=re.IGNORECASE)
        )
