from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import get_configuration, Config, ConfigSetup
import data_converter.data_converter as data_converter
import pathlib
import os
import sys
import pickle
from loguru import logger
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

class DirectoryWatcher:
    def __init__(self, watch_directory, data_file_path) -> None:
        self.watch_directory = watch_directory
        self.data_file_path = data_file_path
        self.baseline_directories_list: list[str] = []
        try:
            with open(self.data_file_path, "rb") as f:
                try:
                    self.baseline_directories_list = pickle.load(f)
                    logger.info("Using existing directories list file")
                except EOFError:
                    raise FileNotFoundError
        except FileNotFoundError:
            logger.info("Directories list file empty/not found, scanning new baseline")
            self.baseline_directories_list = self._scan_watch_directory()
            self._save_directory_baseline(self.baseline_directories_list)
    
    def find_new_directories(self) -> list[str]:
        """Refreshes directory baseline and returns any new directories that did not exist on the old baseline"""
        new_baseline = self._scan_watch_directory()
        new_directories = self._compare_directories_lists(self.baseline_directories_list, new_baseline)
        
        self.baseline_directories_list = new_baseline
        self._save_directory_baseline(new_baseline)
        return new_directories
        
    def _scan_watch_directory(self):
        """Scans the watch directory and returns new baseline"""
        directories = [f.path for f in os.scandir(self.watch_directory) if f.is_dir()]
        logger.debug(f"Scanned directories in watch_folder: {directories}")
        return directories

    def _save_directory_baseline(self, new_baseline):
        """Saves the given baseline to the data file"""
        with open(self.data_file_path, "wb") as f:
            pickle.dump(new_baseline, f)
            logger.debug(f"Overwrote new directory baseline to {self.data_file_path}")

    def _compare_directories_lists(self, old_list: list[str], new_list: list[str]) -> list[str]:
        """Compares a baseline list of directories to a new list and returns all new directories"""
        new_directories = list(set(new_list).difference(old_list)) # everything in new that isn't in old
        return new_directories
   

def initialize_default_data_converter() -> tuple[Config, ConfigSetup]:
    config_setup = load_config_setup()
    config = get_configuration({}, config_setup, None)
    return config, config_setup

if __name__ == "__main__":
    config, config_setup = initialize_default_data_converter()
    dir_watcher = DirectoryWatcher(watch_directory, directories_list_file)
    new_directories_list = dir_watcher.find_new_directories()
    logger.info(f"New directories list: {new_directories_list}")
    new_exp_ids = [pathlib.Path(dir).parts[-1] for dir in new_directories_list]
    print(f"New experiment IDs found: {new_exp_ids}")

    print("Converting Experiments...")
    data_converter.convert_neutron_data(
        config,
        config_setup,
        sources=new_directories_list,
        destination=target_directory
    )
