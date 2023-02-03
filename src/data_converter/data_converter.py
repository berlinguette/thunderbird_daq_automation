import logging
from pathlib import Path
from shutil import rmtree
from typing import List, Optional

from distributed import Client

from data_converter.conversion.data_converter_factory import \
    DataConverterFactory
from data_converter.conversion.support.enums import ExperimentType
from data_converter.utilities.logging import get_conversion_logfile_path
from utilities.utilities.check_type import get_and_check
from utilities.utilities.configuration.configuration import Config, ConfigSetup
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)

logger = logging.getLogger('main')
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)
screen_only_messenger = Messenger(logger, in_log=False)


def convert_neutron_data(
    config: Config,
    config_setup: ConfigSetup,
    sources: Optional[List[str]] = None,
    destination: Optional[str] = None
):
    """Runs the neutron data conversion process:
        - Running the folder picker GUI if needed
        - Iterating over given folders
        - Generating appropriate Converters
        - Performing data conversion, giving user feedback throughout the process

        Parameters
        ----------
        config : Config
            Configuration data. See configuration.py for more info
        config_setup : ConfigSetup
            Configuration setup data
        sources : Optional[List[str]], optional, default None
            location of the experiment folder from command line arguments.
            (This can also be the `raw_data` folder, or any of its subfolders.)
            If not provided, the UI window will be launched.
        destination : Optional[str], optional
            destination folder for data conversion.
            Converted data folders are saved as separate subfolders.
            If not provided, this must be selected in the GUI.
        """
    destination_path: Optional[Path] = None
    if destination is not None:
        destination_path = Path(destination)
    if sources is None:
        from data_converter.ui.converter_gui import converter_gui
        config, source_paths, destination_path = converter_gui(
            config, config_setup)
    else:
        source_paths = [Path(source) for source in sources]
        if destination_path is None:
            destination_path = Path.home()

    if source_paths is not None:
        fresh_destination = get_and_check(
            config, bool, 'fresh_destination', False)
        if fresh_destination and destination_path.is_dir():
            log_only_messenger.debug(
                f'Deleting destination {destination_path}')
            rmtree(destination_path)

        source_count = len(source_paths)
        converter_factory = DataConverterFactory()
        dask_client = None
        for source_idx, source_path in enumerate(source_paths):
            if source_path.is_dir():
                converter_dest = destination_path / source_path.name
            else:
                converter_dest = destination_path / source_path.parent.name
            try:
                converter, exp_type = converter_factory.make_converter(
                    source_path, config, config_setup, converter_dest)
            except ValueError as err:
                logfile_path = get_conversion_logfile_path(destination_path)
                destination_path.mkdir(parents=True, exist_ok=True)
                setup_logger(logger, logfile_path)
                messenger.info(
                    f"Selected folder {source_path} is not a valid experiment folder")
                log_only_messenger.debug(str(err))
                continue

            converter.messenger.info(
                f'Converting source {source_idx+1}/{source_count}:' +
                f' {converter.experiment_root}'
            )
            if dask_client is None and exp_type == ExperimentType.CAEN:
                dask_client = Client()
            result = converter.convert()
            if not result:
                converter.messenger.info(
                    f'Conversion of source #{source_idx} at {source_path}' +
                    ' could not be completed'
                )

        messenger.info("All conversions complete!")
        cleanup_logger(logger)
        text_ui = get_and_check(config, bool, 'text_ui', False)
        if text_ui:
            input("Press Enter to close window")
    else:
        print('Closing...')
