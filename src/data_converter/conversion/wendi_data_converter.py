from pathlib import Path
from typing import Dict

from utilities.utilities.check_type import get_and_check
from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.wendi_log_to_parquet import \
    convert_wendi_log_to_parquet

KEY_DATASET_ROOT = 'dataset_root'
KEY_DATASET_RAW = 'dataset_raw_data'
KEY_DATASET_RAW_WENDI = 'dataset_raw_wendi'
KEY_DATASET_PROCESSED = 'dataset_processed_data'
KEY_DATASET_UNFILTERED = 'dataset_processed_unfiltered'
KEY_DATASET_UNFILTERED_WENDI = 'dataset_unfiltered_wendi'


class WendiDataConverter(AbstractDataConverter):
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
        # source paths are fine
        # need dataset_raw, raw_log for original file
        # need dataset_processed, proc_unfiltered, unfiltered_wendi for converted
        dataset_raw_folder = self._destination.joinpath(
            constants.DATASET_RAW_DATA_FOLDER_NAME)
        dataset_raw_log_folder = dataset_raw_folder.joinpath(
            constants.WENDI_DATASET_SUBFOLDER_NAME)
        dataset_processed_folder = self._destination.joinpath(
            constants.DATASET_PROCESSED_DATA_FOLDER_NAME)
        dataset_proc_unfil_folder = dataset_processed_folder.joinpath(
            constants.CAEN_PROCESSED_UNFILTERED_FOLDER_NAME)
        dataset_unfiltered_wendi_folder = dataset_proc_unfil_folder.joinpath(
            constants.WENDI_DATASET_SUBFOLDER_NAME)
        return {
            KEY_DATASET_ROOT: self._destination,
            KEY_DATASET_RAW: dataset_raw_folder,
            KEY_DATASET_RAW_WENDI: dataset_raw_log_folder,
            KEY_DATASET_PROCESSED: dataset_processed_folder,
            KEY_DATASET_UNFILTERED: dataset_proc_unfil_folder,
            KEY_DATASET_UNFILTERED_WENDI: dataset_unfiltered_wendi_folder
        }

    def _prepare_dataset_destinations(self, paths: Dict[str, Path]):
        dataset_raw_folder = paths[KEY_DATASET_RAW]
        dataset_raw_wendi_folder = paths[KEY_DATASET_RAW_WENDI]
        dataset_processed_folder = paths[KEY_DATASET_PROCESSED]
        dataset_unfiltered_folder = paths[KEY_DATASET_UNFILTERED]
        dataset_unfiltered_wendi_folder = paths[KEY_DATASET_UNFILTERED_WENDI]

        self._messenger.info('Preparing destination folders')
        self._prepare_destinations([
            dataset_raw_folder,
            dataset_raw_wendi_folder])
        self._messenger.info(' - Raw WENDI log destination done')
        self._prepare_destinations([
            dataset_processed_folder,
            dataset_unfiltered_folder,
            dataset_unfiltered_wendi_folder])
        self._messenger.info(' - Converted WENDI log destination done')

        self._screen_only_messenger.info('')

    def _conversion_process(self, paths: Dict[str, Path]):
        dataset_raw_wendi_folder = paths[KEY_DATASET_RAW_WENDI]
        dataset_unfiltered_wendi_folder = paths[KEY_DATASET_UNFILTERED_WENDI]

        self._messenger.info("Converting WENDI log to Parquet")
        converted_name = f'wendi_{self._experiment_source.stem}.parquet'
        converted_dest = dataset_unfiltered_wendi_folder / converted_name
        convert_wendi_log_to_parquet(
            self._experiment_source, converted_dest, self._logfile_path)
        self._screen_only_messenger.info('')

        self._messenger.info("Moving original WENDI log to destination")
        move_files = get_and_check(self._config, bool, 'move_files', False)
        raw_dest = dataset_raw_wendi_folder / self._experiment_source.name
        # self._experiment_source.rename(raw_dest)
        self._handle_raw_file(self._experiment_source,
                              raw_dest,
                              move_file=move_files)
        self._screen_only_messenger.info('')
