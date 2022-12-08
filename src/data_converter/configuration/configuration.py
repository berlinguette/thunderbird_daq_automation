from pathlib import Path

from utilities.utilities.configuration.configuration import (
    ConfigSetup, _load_yaml_dict_file)


def load_config_setup() -> ConfigSetup:
    """Loads the configuration setup file

    Returns
    -------
    Dict
        configuration setup data
    """
    # assumes setup file is in same dir as this .py file
    setup_file_path = Path(__file__).parent / 'config_fields_setup.yaml'
    return _load_yaml_dict_file(setup_file_path)
