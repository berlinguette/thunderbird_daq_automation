from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
    Config,
    ConfigSetup,
)
import data_converter.data_converter as data_converter
from automatic_converter.directory_watcher import DirectoryWatcher
import pathlib
import sys
from loguru import logger
from flask import Flask
# import logging

logger.remove()
logger.add(sys.stderr, level="WARNING")
# logging.basicConfig(level=logging.DEBUG)

watch_directory = "/mnt/qmi-share/daniel_test_data/1-Unconverted_Data"
target_directory = "/mnt/qmi-share/daniel_test_data/2-Converted_Data"
# watch_folder = "Q:/Neutron Data/1-Unconverted_Data"
# target_folder = "Q:/Neutron Data/2-Converted_Data"

package_dir = pathlib.Path(__file__).parent.absolute()
directories_list_file = pathlib.Path(package_dir, "../data/directories.pkl")


def initialize_default_data_converter() -> tuple[Config, ConfigSetup]:
    config_setup = load_config_setup()
    config = get_configuration({}, config_setup, None)
    return config, config_setup


def create_app():
    app = Flask(__name__)
    config, config_setup = initialize_default_data_converter()
    dir_watcher = DirectoryWatcher(watch_directory, directories_list_file)

    @app.post("/")
    def rescan_directory():
        logger.info("Rescan triggered")
        new_directories_list = dir_watcher.find_new_directories()
        logger.info(f"New directories list: {new_directories_list}")
        new_exp_ids = [pathlib.Path(dir).parts[-1] for dir in new_directories_list]
        print(f"New experiment IDs found: {new_exp_ids}")

        print("Converting Experiments...")
        data_converter.convert_neutron_data(
            config, config_setup, sources=new_directories_list, destination=target_directory
        )

        return {
            "new_experiments": new_exp_ids
        }
    
    return app

if __name__ == "__main__":
   app = create_app()
   app.run(debug=True)
