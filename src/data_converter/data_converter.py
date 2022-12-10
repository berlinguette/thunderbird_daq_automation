import logging
from pathlib import Path
from typing import Optional

from data_converter.conversion.data_converter_factory import \
    DataConverterFactory
from data_converter.ui.converter_gui import converter_gui
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
    folder_str: Optional[str] = None
):
    """Runs the neutron data conversion process:
    - Running the folder picker GUI if needed
    - Iterating over given folders
    - Generating appropriate Converters
    - Performing data conversion, giving user feedback throughout the process

    Parameters
    ----------
    config : Dict
        Configuration data. See configuration.py for more info
    config_setup: Dict[str, Any]
        Configuration setup data
    folder_str : Optional[str], optional
        location of the experiment folder from command line arguments.
        (This can also be the `raw_data` folder, or any of its subfolders.)
        If not provided, the UI window will be launched.
    """
    if folder_str is None:
        config, folder_paths, destination = converter_gui(config, config_setup)
    else:
        folder_paths = [Path(folder_str)]
        destination = Path.home()

    if folder_paths is not None:
        folders_count = len(folder_paths)
        converter_factory = DataConverterFactory()
        for folder_i, folder_path in enumerate(folder_paths):
            try:
                converter = converter_factory.make_converter(
                    folder_path, config, config_setup, destination)
            except ValueError as err:
                setup_logger(logger, folder_path)
                messenger.info(
                    f"Selected folder {folder_path} is not a valid experiment folder")
                log_only_messenger.debug(str(err))
                continue

            converter.messenger.info(
                f'Converting files in folder {folder_i+1}/{folders_count}:' +
                f' {converter.experiment_root}'
            )
            result = converter.convert()
            if not result:
                converter.messenger.info(
                    f'Conversion of folder #{folder_i} at {folder_path}'+
                    ' could not be completed'
                )

        messenger.info("All conversions complete!")
        cleanup_logger(logger)
        input("Press Enter to close window")
    else:
        print('Closing...')
