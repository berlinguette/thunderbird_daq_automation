from automatic_converter.experiment_tracker import ExperimentTracker
from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
    Config,
    ConfigSetup,
)
import data_converter.data_converter as data_converter
from automatic_converter.directory_watcher import DirectoryWatcher
from pathlib import Path
import pickle
from loguru import logger
from flask import Flask, request
import sys
# import logging

logger.remove()
logger.add(sys.stderr, level="INFO")
# logging.basicConfig(level=logging.DEBUG)

neutron_data_path = "/mnt/qmi-share/Neutron Data/"
# neutron_data_path = "/mnt/qmi-share/daniel_test_data"

unconverted_data_dir = Path(neutron_data_path, "1-Unconverted_Data")
converted_data_dir = Path(neutron_data_path, "2-Converted_Data")
processed_data_dir = Path(neutron_data_path, "3-Output")
# watch_folder = "Q:/Neutron Data/1-Unconverted_Data"
# target_folder = "Q:/Neutron Data/2-Converted_Data"

package_dir = Path(__file__).parent.absolute()
directories_list_file = Path(package_dir, "../data/directories.pkl")

def initialize_default_data_converter() -> tuple[Config, ConfigSetup]:
    config_setup = load_config_setup()
    config = get_configuration({}, config_setup, None)
    return config, config_setup


def create_app():
    app = Flask(__name__)
    config, config_setup = initialize_default_data_converter()
    baseline_directories_list: list[str]|None = None
    try:
        with open(directories_list_file, "rb") as f:
            baseline_directories_list = pickle.load(f)
    except FileNotFoundError:
        pass

    dir_watcher = DirectoryWatcher(unconverted_data_dir, baseline_directories_list)
    exp_tracker = ExperimentTracker(unconverted_data_dir, converted_data_dir, processed_data_dir)

    @app.get("/inventory")
    def get_inventory():
        exp_filter = request.args.get('filter')
        get_exp_mapping = {
            "": exp_tracker.get_all_experiments,
            "to_be_converted": exp_tracker.get_all_to_convert,
            "to_be_processed": exp_tracker.get_all_to_process
        }
        if exp_filter not in get_exp_mapping:
            return "Invalid experiment filter"
        logger.info(f"Filtering inventory by {exp_filter}")
        return [exp.to_dict() for exp in get_exp_mapping[exp_filter]()]

    @app.post("/inventory")
    def refresh_inventory():
        exp_tracker.refresh_all()
        # experiments_to_convert = exp_tracker.get_all_to_convert()

        return [exp.to_dict() for exp in exp_tracker.get_all_experiments()]

    @app.post("/")
    def rescan_directory():
        logger.info("Rescan triggered")
        new_directories_list = dir_watcher.find_new_directories()
        logger.info(f"New directories list: {new_directories_list}")
        new_exp_ids = [Path(dir).parts[-1] for dir in new_directories_list]
        print(f"New experiment IDs found: {new_exp_ids}")

        print("Converting Experiments...")

        for new_directory in new_directories_list:
            data_converter.convert_neutron_data(
                config, config_setup, sources=[new_directory], destination=converted_data_dir
            )



        return {
            "new_experiments": new_exp_ids
        }
    
    return app

if __name__ == "__main__":
   app = create_app()
   app.run(debug=True)
