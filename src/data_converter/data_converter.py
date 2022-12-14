import logging
from pathlib import Path
from shutil import rmtree
from typing import Optional

from data_converter.conversion.data_converter_factory import \
    DataConverterFactory
from data_converter.ui.converter_gui import converter_gui
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
        config, sources, destination = converter_gui(config, config_setup)
    else:
        sources = [Path(folder_str)]
        destination = Path.home()

    if sources is not None:
        fresh_destination = get_and_check(
            config, bool, 'fresh_destination', False)
        if fresh_destination and destination.is_dir():
            log_only_messenger.debug(
                f'Deleting destination {destination}')
            rmtree(destination)

        source_count = len(sources)
        converter_factory = DataConverterFactory()
        for source_idx, source_path in enumerate(sources):
            if source_path.is_dir():
                converter_dest = destination / source_path.name
            else:
                converter_dest = destination / source_path.parent.name
            try:
                converter = converter_factory.make_converter(
                    source_path, config, config_setup, converter_dest)
            except ValueError as err:
                logfile_path = get_conversion_logfile_path(source_path)
                setup_logger(logger, logfile_path)
                messenger.info(
                    f"Selected folder {source_path} is not a valid experiment folder")
                log_only_messenger.debug(str(err))
                continue

            converter.messenger.info(
                f'Converting files in folder {source_idx+1}/{source_count}:' +
                f' {converter.experiment_root}'
            )
            result = converter.convert()
            if not result:
                converter.messenger.info(
                    f'Conversion of folder #{source_idx} at {source_path}' +
                    ' could not be completed'
                )

        messenger.info("All conversions complete!")
        cleanup_logger(logger)
        input("Press Enter to close window")
    else:
        print('Closing...')
