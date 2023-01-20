from argparse import ArgumentParser
from multiprocessing import freeze_support
from typing import Any, Dict, List, Optional

from data_converter.configuration.configuration import load_config_setup
from data_converter.data_converter import convert_neutron_data
from utilities.utilities.configuration.configuration import (
    get_configuration, populate_args_parser)
from utilities.utilities.packaging.packaging import (finish_splash_screen,
                                                     is_pyinstaller_app,
                                                     is_using_pyinst_splash)
from VERSION import VERSION


def _setup_parser(config_setup: Dict[str, Any]) -> ArgumentParser:
    """Produces ArgumentParser with all needed arguments

    Returns
    -------
    ArgumentParser
        ArgumentParser configured with all supported command line arguments
    """
    parser = ArgumentParser(
        prog="Experimental Data Converter",
        description=("Converts raw data files from experiment"
                     " to Parquet files"))
    parser = populate_args_parser(parser, config_setup)

    return parser


if __name__ == "__main__":
    if is_pyinstaller_app() and is_using_pyinst_splash():
        finish_splash_screen(final_text=f"Finished loading - v{VERSION}")

    freeze_support()  # needed for Windows multiprocessing/processpool

    config_setup = load_config_setup()
    parser = _setup_parser(config_setup)

    args = parser.parse_args()
    args_dict = vars(args)
    # source and config are only needed here, not in config
    source_paths: Optional[List[str]] = args_dict.pop('sources', None)
    config_path: Optional[str] = args_dict.pop('config', None)
    dest_path: Optional[str] = args_dict.pop('destination', None)
    config = get_configuration(args_dict, config_setup, config_path)

    convert_neutron_data(
        config,
        config_setup,
        sources=source_paths,
        destination=dest_path
    )
