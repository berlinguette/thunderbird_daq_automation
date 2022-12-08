from email.contentmanager import raw_data_manager
from shutil import rmtree

from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.support.constants import (
    DATASET_PARQUET_FOLDER_NAME, DATASET_RAW_DATA_FOLDER_NAME,
    PICO_MATLAB_FOLDER_NAME, PICO_PSDATA_FOLDER_NAME)
from data_converter.conversion.support.matlab_parquetizer import \
    parquetize_directory
from data_converter.conversion.support.psdata_to_matlab import \
    convert_psdata_directory
from utilities.utilities.check_type import get_and_check
from utilities.utilities.logging_helpers.setup_logger import cleanup_logger
from pathlib import Path


class PicoDataConverter(AbstractDataConverter):
    def convert(self) -> bool:
        try:
            # raw_data_folder = self._experiment_root / DATASET_RAW_DATA_FOLDER_NAME
            # psdata_folder = raw_data_folder / PICO_PSDATA_FOLDER_NAME
            # matlab_folder = raw_data_folder / PICO_MATLAB_FOLDER_NAME
            # parquet_folder = raw_data_folder / DATASET_PARQUET_FOLDER_NAME
            psdata_folder, *rest = self._determine_paths()
            matlab_folder, parquet_folder = rest

            self._initial_messages()
            self._prepare_dataset_destinations(matlab_folder, parquet_folder)
            self._conversion_process(
                psdata_folder, matlab_folder, parquet_folder)

            self._finish_conversion()
            return True
        except Exception as err:
            # self._log_exception(err)
            self._logger.exception(err)
            return False

    def _determine_paths(self):
        raw_data_folder = self._experiment_root / DATASET_RAW_DATA_FOLDER_NAME
        psdata_folder = raw_data_folder / PICO_PSDATA_FOLDER_NAME
        matlab_folder = raw_data_folder / PICO_MATLAB_FOLDER_NAME
        parquet_folder = raw_data_folder / DATASET_PARQUET_FOLDER_NAME
        return psdata_folder, matlab_folder, parquet_folder

    def _prepare_dataset_destinations(self, matlab_folder: Path, parquet_folder: Path):
        fresh_destination = get_and_check(
            self._config, bool, 'fresh_destination', False)
        self._messenger.info('Preparing destination folders')
        self._prepare_destinations(matlab_folder, fresh_destination)
        self._messenger.debug(' - Matlab destination done')
        self._prepare_destinations(parquet_folder, fresh_destination)
        self._messenger.debug(' - Parquet destination done')
        self._screen_only_messenger.info('')

    def _conversion_process(
        self, psdata_folder: Path, matlab_folder: Path, parquet_folder: Path
    ):
        self._messenger.info("Converting PSData to Matlab")
        self._screen_only_messenger.info(
            "You might see other windows pop up quickly. " +
            "This is normal. Don't panic!"
        )
        convert_psdata_directory(
            psdata_folder, matlab_folder, self._config)
        self._screen_only_messenger.info('')
        self._messenger.info("Converting Matlab to Parquet")
        parquetize_directory(matlab_folder, parquet_folder, self._config)

        if not self._config.get('keep_matlab'):
            self._screen_only_messenger.info('')
            self._messenger.info("Removing Matlab files")
            rmtree(matlab_folder)
