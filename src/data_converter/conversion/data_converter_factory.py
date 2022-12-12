import re
from pathlib import Path

from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.caen_data_converter import CaenDataConverter
from data_converter.conversion.pico_data_converter import PicoDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.experiment_type import ExperimentType
from data_converter.conversion.wendi_data_converter import WendiDataConverter
from utilities.utilities.configuration.configuration import Config, ConfigSetup

PICO_RAW_DATA_FOLDERS = (
    constants.PICO_PSDATA_FOLDER_NAME,
    constants.DATASET_PARQUET_FOLDER_NAME,
    constants.PICO_MATLAB_FOLDER_NAME
)
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
    ) -> AbstractDataConverter:
        found_schema = self._determine_data_schema(exp_folder)
        if found_schema is None:
            raise ValueError(
                f"Experiment root could not be found for folder {exp_folder}")
        exp_type, exp_root = found_schema
        if exp_type == ExperimentType.PICO:
            return PicoDataConverter(exp_root, config, config_setup, destination)
        elif exp_type == ExperimentType.CAEN:
            return CaenDataConverter(exp_root, config, config_setup, destination)
        elif exp_type == ExperimentType.WENDI:
            return WendiDataConverter(exp_root, config, config_setup, destination)
        else:
            raise ValueError(f"Invalid experiment type {exp_type}")

    def _find_pico_root(
        self, source_path: Path, found_psdata: bool = False, found_pico_rawdata: bool = False
    ) -> Path | None:
        root_path = None
        if not source_path.is_dir():
            return self._find_pico_root(source_path.parent)
        if source_path.name in PICO_RAW_DATA_FOLDERS:
            is_psdata_folder = source_path.name == constants.PICO_PSDATA_FOLDER_NAME
            if (is_psdata_folder and
                    not self._are_psdata_files_here(source_path)):
                return None
            root_path = self._find_pico_root(
                source_path.parent, found_psdata=is_psdata_folder)
        elif source_path.name == constants.DATASET_RAW_DATA_FOLDER_NAME:
            checks = [
                (source_path / constants.PICO_RAW_DATA_METADATA_FILE).exists(),
                found_psdata or (
                    source_path / constants.PICO_PSDATA_FOLDER_NAME).exists()
            ]
            if all(checks):
                root_path = self._find_pico_root(
                    source_path.parent,
                    found_psdata=found_psdata,
                    found_pico_rawdata=True
                )
            pass
        else:
            psdata_folder = source_path.joinpath(
                constants.DATASET_RAW_DATA_FOLDER_NAME,
                constants.PICO_PSDATA_FOLDER_NAME)
            checks = [
                ((source_path / constants.DATASET_METADATA_FILE_TXT).exists() or
                 (source_path / constants.DATASET_METADATA_FILE_TOML).exists()),
                found_pico_rawdata or (
                    source_path / constants.DATASET_RAW_DATA_FOLDER_NAME
                ).exists(),
                found_psdata or (
                    psdata_folder.exists() and
                    self._are_psdata_files_here(psdata_folder)),
            ]
            if all(checks):
                root_path = source_path
        return root_path

    def _find_caen_root(
        self, source_path: Path, found_subfolder: None | str = None
    ) -> Path | None:
        root_path = None
        if not source_path.is_dir():
            return self._find_caen_root(source_path.parent)
        if source_path.name in CAEN_RAW_DATA_FOLDERS:
            found_subfolder = source_path.name
            if source_path.name == constants.CAEN_RAW_FOLDER_NAME:
                data_file_pattern = re.compile(r'SDataR_.*\.[Cc][Ss][Vv]$)')
                if not self._does_matching_file_exist(
                        source_path, data_file_pattern):
                    return None
            elif source_path.name == constants.CAEN_FILTERED_FOLDER_NAME:
                data_file_pattern = re.compile(r'SDataF_.*\.[Cc][Ss][Vv]$')
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
                check_caen_subfolder(constants.CAEN_OFFLINE_FOLDER_NAME),
                check_caen_subfolder(constants.CAEN_RAW_FOLDER_NAME),
                check_caen_subfolder(constants.CAEN_SCREENSHOTS_FOLDER_NAME),
                check_caen_subfolder(constants.CAEN_UNFILTERED_FOLDER_NAME)
            ]
            if all(checks):
                root_path = source_path
        return root_path

    def _is_wendi_logfile(self, source_path: Path) -> bool:
        if source_path.is_file() and source_path.suffix.lower() == '.log':
            with open(source_path, 'r') as source_file:
                line = source_file.readline()
            model_number = line[:5]
            return model_number == "FH40G"
        return False

    def _determine_data_schema(
        self,
        source_path: Path
    ) -> tuple[ExperimentType, Path] | None:
        if self._is_wendi_logfile(source_path):
            return ExperimentType.WENDI, source_path

        root_path = self._find_pico_root(source_path)
        if root_path is not None:
            return ExperimentType.PICO, root_path

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
