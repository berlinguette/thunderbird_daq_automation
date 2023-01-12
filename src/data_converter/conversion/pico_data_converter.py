from email.contentmanager import raw_data_manager
from pathlib import Path
from shutil import rmtree

from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.matlab_parquetizer import \
    parquetize_directory
from data_converter.conversion.support.psdata_to_matlab import \
    convert_psdata_directory
from utilities.utilities.check_type import get_and_check

KEY_PSDATA = 'source_psdata'
KEY_DATASET_RAW = 'dataset_raw_data'
KEY_DATASET_PSDATA = 'dataset_raw_data_psdata'
KEY_DATASET_MATLAB = 'dataset_raw_data_matlab'
KEY_DATASET_PARQUET = 'dataset_raw_data_parquet'


class PicoDataConverter(AbstractDataConverter):
    # TODO DEPRECATED Remove in v4.0.0
    def convert(self) -> bool:
        self._messenger.warning(
            "DEPRECATION WARNING: PSData conversion will be removed in v4.0.0")
        try:
            paths_dict = self._determine_paths()

            self._initial_messages()
            self._prepare_dataset_destinations(paths_dict)
            self._conversion_process(paths_dict)

            self._finish_conversion()
            return True
        except Exception as err:
            # self._log_exception(err)
            self._logger.exception(err)
            return False

    def _determine_paths(self) -> dict[str, Path]:
        # TODO how to use self._destination here?
        raw_data_folder = self._experiment_source.joinpath(
            constants.DATASET_RAW_DATA_FOLDER_NAME)
        source_psdata_folder = raw_data_folder.joinpath(
            constants.PICO_PSDATA_FOLDER_NAME)
        dataset_raw_data_folder = self._destination.joinpath(
            constants.DATASET_RAW_DATA_FOLDER_NAME)
        dataset_psdata_folder = dataset_raw_data_folder.joinpath(
            constants.PICO_PSDATA_FOLDER_NAME)
        dataset_matlab_folder = dataset_raw_data_folder.joinpath(
            constants.PICO_MATLAB_FOLDER_NAME)
        dataset_parquet_folder = dataset_raw_data_folder.joinpath(
            constants.DATASET_PARQUET_FOLDER_NAME)
        return {
            KEY_DATASET_RAW: dataset_raw_data_folder,
            KEY_PSDATA: source_psdata_folder,
            KEY_DATASET_PSDATA: dataset_psdata_folder,
            KEY_DATASET_MATLAB: dataset_matlab_folder,
            KEY_DATASET_PARQUET: dataset_parquet_folder
        }

    def _prepare_dataset_destinations(self, paths_dict: dict[str, Path]):
        dataset_raw_data_folder = paths_dict[KEY_DATASET_RAW]
        matlab_folder = paths_dict[KEY_DATASET_MATLAB]
        parquet_folder = paths_dict[KEY_DATASET_PARQUET]
        self._messenger.info('Preparing destination folders')
        self._prepare_destinations(
            [dataset_raw_data_folder, matlab_folder])
        self._messenger.debug(' - Matlab destination done')
        self._prepare_destinations(parquet_folder)
        self._messenger.debug(' - Parquet destination done')
        self._screen_only_messenger.info('')

    def _conversion_process(self, paths_dict: dict[str, Path]):
        source_psdata_folder = paths_dict[KEY_PSDATA]
        dataset_psdata_folder = paths_dict[KEY_DATASET_PSDATA]
        dataset_matlab_folder = paths_dict[KEY_DATASET_MATLAB]
        dataset_parquet_folder = paths_dict[KEY_DATASET_PARQUET]
        self._messenger.info("Converting PSData to Matlab")
        self._screen_only_messenger.info(
            "You might see other windows pop up quickly. " +
            "This is normal. Don't panic!"
        )
        convert_psdata_directory(
            source_psdata_folder, dataset_matlab_folder, self._config)
        self._screen_only_messenger.info('')
        self._messenger.info("Converting Matlab to Parquet")
        parquetize_directory(dataset_matlab_folder,
                             dataset_parquet_folder, self._config)
        self._messenger.info("Moving PSData to destination")
        for file in source_psdata_folder.iterdir():
            if file.is_file() and file.suffix.lower() == ".psdata":
                file.rename(dataset_psdata_folder / file.name)

        if not self._config.get('keep_matlab'):
            self._screen_only_messenger.info('')
            self._messenger.info("Removing Matlab files")
            rmtree(dataset_matlab_folder)
