import re
from datetime import datetime
from pathlib import Path

import tomli_w
from distributed import Client

from data_converter.conversion.abstract_data_converter import \
    AbstractDataConverter
from data_converter.conversion.support import constants
from data_converter.conversion.support.csv_to_parquet import \
    convert_csv_folder_to_parquet
from data_converter.conversion.support.spectrum_to_parquet import \
    convert_spectra_to_parquet
from utilities.utilities.check_type import get_and_check

KEY_RAW_DATA = 'raw_data_folder'
KEY_FILTERED_DATA = 'filtered_data_folder'
KEY_UNFILTERED_DATA = 'unfiltered_data_folder'
KEY_DATASET_ROOT = 'dataset_root'
KEY_DATASET_RAW = 'dataset_raw_data'
KEY_DATASET_RAW_CSV = 'dataset_raw_data_csv'
KEY_DATASET_RAW_PARQUET = 'dataset_raw_data_parquet'
KEY_DATASET_PROCESSED = 'dataset_processed_data'
KEY_DATASET_FILTERED = 'dataset_processed_filtered'
KEY_DATASET_FILTERED_PSD = 'dataset_filtered_psd'
KEY_DATASET_FILTERED_SIGNALS = 'dataset_filtered_signals'
KEY_DATASET_FILTERED_SPECTRA = 'dataset_filtered_spectra'
KEY_DATASET_UNFILTERED = 'dataset_processed_unfiltered'
KEY_DATASET_UNFILTERED_PSD = 'dataset_unfiltered_psd'
KEY_DATASET_UNFILTERED_SIGNALS = 'dataset_unfiltered_signals'
KEY_DATASET_UNFILTERED_SPECTRA = 'dataset_unfiltered_spectra'


class CaenDataConverter(AbstractDataConverter):
    def convert(self) -> bool:
        client = Client()
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

    def _determine_paths(self) -> dict[str, Path]:
        raw_data_folder = self._experiment_source.joinpath(
            constants.CAEN_RAW_FOLDER_NAME)
        filtered_data_folder = self._experiment_source.joinpath(
            constants.CAEN_FILTERED_FOLDER_NAME)
        unfiltered_data_folder = self._experiment_source.joinpath(
            constants.CAEN_UNFILTERED_FOLDER_NAME)
        # dataset_root_folder = (self._destination /
        #                        self._experiment_root.name)
        dataset_raw_folder = self._destination.joinpath(
            constants.DATASET_RAW_DATA_FOLDER_NAME)
        dataset_raw_csv_folder = dataset_raw_folder.joinpath(
            constants.CAEN_RAW_FOLDER_NAME)
        dataset_raw_parquet_folder = dataset_raw_folder.joinpath(
            constants.DATASET_PARQUET_FOLDER_NAME)
        dataset_processed_folder = self._destination.joinpath(
            constants.DATASET_PROCESSED_DATA_FOLDER_NAME)
        dataset_filtered_folder = dataset_processed_folder.joinpath(
            constants.CAEN_PROCESSED_FILTERED_FOLDER_NAME)
        dataset_filtered_psd_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_PSD_FOLDER_NAME)
        dataset_filtered_signals_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_SIGNALS_FOLDER_NAME)
        dataset_filtered_spectra_folder = dataset_filtered_folder.joinpath(
            constants.CAEN_PROCESSED_SPECTRA_FOLDER_NAME)
        dataset_unfiltered_folder = dataset_processed_folder.joinpath(
            constants.CAEN_PROCESSED_UNFILTERED_FOLDER_NAME)
        dataset_unfiltered_psd_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_PSD_FOLDER_NAME)
        dataset_unfiltered_signals_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_SIGNALS_FOLDER_NAME)
        dataset_unfiltered_spectra_folder = dataset_unfiltered_folder.joinpath(
            constants.CAEN_PROCESSED_SPECTRA_FOLDER_NAME)
        return {
            KEY_RAW_DATA: raw_data_folder,
            KEY_FILTERED_DATA: filtered_data_folder,
            KEY_UNFILTERED_DATA: unfiltered_data_folder,
            KEY_DATASET_ROOT: self._destination,
            KEY_DATASET_RAW: dataset_raw_folder,
            KEY_DATASET_RAW_CSV: dataset_raw_csv_folder,
            KEY_DATASET_RAW_PARQUET: dataset_raw_parquet_folder,
            KEY_DATASET_PROCESSED: dataset_processed_folder,
            KEY_DATASET_FILTERED: dataset_filtered_folder,
            KEY_DATASET_FILTERED_PSD: dataset_filtered_psd_folder,
            KEY_DATASET_FILTERED_SIGNALS: dataset_filtered_signals_folder,
            KEY_DATASET_FILTERED_SPECTRA: dataset_filtered_spectra_folder,
            KEY_DATASET_UNFILTERED: dataset_unfiltered_folder,
            KEY_DATASET_UNFILTERED_PSD: dataset_unfiltered_psd_folder,
            KEY_DATASET_UNFILTERED_SIGNALS: dataset_unfiltered_signals_folder,
            KEY_DATASET_UNFILTERED_SPECTRA: dataset_unfiltered_spectra_folder,
        }

    def _prepare_dataset_destinations(
        self,
        paths: dict[str, Path]
    ):
        dataset_root_folder = paths[KEY_DATASET_ROOT]
        dataset_raw_folder = paths[KEY_DATASET_RAW]
        dataset_raw_csv_folder = paths[KEY_DATASET_RAW_CSV]
        dataset_processed_folder = paths[KEY_DATASET_PROCESSED]
        dataset_unfiltered_folder = paths[KEY_DATASET_UNFILTERED]
        dataset_unfiltered_folder_psd = paths[KEY_DATASET_UNFILTERED_PSD]
        dataset_unfiltered_signals_folder = paths[KEY_DATASET_UNFILTERED_SIGNALS]
        dataset_unfiltered_spectra_folder = paths[KEY_DATASET_UNFILTERED_SPECTRA]

        fresh_destination = get_and_check(
            self._config, bool, 'fresh_destination', False
        )
        self._messenger.info('Preparing destination folders')
        self._prepare_destinations(
            [dataset_root_folder,
                dataset_raw_folder,
                dataset_raw_csv_folder],
            fresh_destination)
        self._messenger.debug(' - Raw CSV destination done')
        self._messenger.debug(' - Raw Parquet destination done')
        self._prepare_destinations(
            [dataset_processed_folder,
                dataset_unfiltered_folder,
                dataset_unfiltered_folder_psd,
                dataset_unfiltered_signals_folder,
                dataset_unfiltered_spectra_folder],
            fresh_destination)
        self._messenger.debug(' - Processed data destination done')

        self._screen_only_messenger.info('')

    def _conversion_process(self,
                            paths: dict[str, Path]
                            ):
        raw_data_folder = paths[KEY_RAW_DATA]
        dataset_raw_folder = paths[KEY_DATASET_RAW]
        dataset_raw_csv_folder = paths[KEY_DATASET_RAW_CSV]
        unfiltered_data_folder = paths[KEY_UNFILTERED_DATA]
        dataset_unfiltered_psd_folder = paths[KEY_DATASET_UNFILTERED_PSD]
        dataset_unfiltered_signals_folder = paths[KEY_DATASET_UNFILTERED_SIGNALS]
        dataset_unfiltered_spectra_folder = paths[KEY_DATASET_UNFILTERED_SPECTRA]

        self._messenger.info("Generating metadata file")
        self._generate_metadata_file(paths)
        self._screen_only_messenger.info('')

        self._messenger.info("Moving raw data files to destination")
        for file in raw_data_folder.iterdir():
            if (file.is_file() and
                    (file.suffix.lower() == '.csv' or
                     file.name == 'settings.xml')):
                file.rename(dataset_raw_csv_folder / file.name)
        self._screen_only_messenger.info('')

        self._messenger.info("Converting unfiltered data to Parquet")
        convert_csv_folder_to_parquet(
            unfiltered_data_folder,
            (dataset_unfiltered_psd_folder, dataset_unfiltered_signals_folder),
            self._config, self._logfile_path)
        convert_spectra_to_parquet(
            unfiltered_data_folder, dataset_unfiltered_spectra_folder, self._logfile_path)
        self._screen_only_messenger.info('')

    def _generate_metadata_file(self, paths: dict[str, Path]):
        dataset_root_folder = paths[KEY_DATASET_ROOT]
        run_info_path = self._experiment_source / 'run.info'
        metadata_dest_path = dataset_root_folder.joinpath(
            constants.DATASET_METADATA_FILE_TOML)

        with open(run_info_path, 'r') as infofile:
            info_lines = infofile.readlines()

        id_pattern = re.compile(r'^id=(.*)$')
        id_matches = [id_pattern.match(line) for line in info_lines]
        id_matches = [match for match in id_matches if match is not None]
        if len(id_matches) == 0:
            raise ValueError(f"Id could not be read from file {run_info_path}")
        id = id_matches[0].group(1)

        start_time_pattern = re.compile(r'^time.start=(.*)$')
        time_matches = [start_time_pattern.match(line) for line in info_lines]
        time_matches = [match for match in time_matches if match is not None]
        if len(time_matches) == 0:
            raise ValueError(
                f"Start time could not be read from file {run_info_path}")
        time_start = time_matches[0].group(1)
        time_start = time_start.replace('/', '-')
        time_start = f'{time_start[:-2]}:{time_start[-2:]}'

        start_datetime = datetime.fromisoformat(time_start)
        start_date_stamp = start_datetime.date().strftime('%Y%m%d')
        metadata = {
            'exp_id': f"{start_date_stamp}_{id}",
            'desc': "<Add Description>",
            'exp_start': start_datetime
        }

        with open(metadata_dest_path, 'wb') as savefile:
            tomli_w.dump(metadata, savefile)
