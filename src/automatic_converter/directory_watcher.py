import os
import pickle
from loguru import logger

class DirectoryWatcher:
    def __init__(self, watch_directory: str, data_file_path: str) -> None:
        """Loads baseline from given data file path or scans and saves new baseline from given watch directory"""
        self.watch_directory = watch_directory
        self.data_file_path = data_file_path
        self.baseline_directories_list: list[str] = []
        try:
            with open(self.data_file_path, "rb") as f:
                try:
                    self.baseline_directories_list = pickle.load(f)
                    logger.info("Using existing directories list file")
                    print("Loading from existing data file...")
                except EOFError:
                    raise FileNotFoundError
        except FileNotFoundError:
            logger.info("Directories list file empty/not found, scanning new baseline")
            print("Generating new baseline...")
            self.baseline_directories_list = self._scan_watch_directory()
            self._save_directory_baseline(self.baseline_directories_list)
    
    def find_new_directories(self, save_to_file = True) -> list[str]:
        """Refreshes directory baseline and returns any new directories that did not exist on the old baseline"""
        new_baseline = self._scan_watch_directory()
        new_directories = self._compare_directories_lists(self.baseline_directories_list, new_baseline)
        
        self.baseline_directories_list = new_baseline
        if save_to_file:
            self._save_directory_baseline(new_baseline)
        return new_directories
        
    def _scan_watch_directory(self) -> list[str]:
        """Scans the watch directory and returns new baseline"""
        directories = [f.path for f in os.scandir(self.watch_directory) if f.is_dir()]
        logger.debug(f"Scanned directories in watch_folder: {directories}")
        return directories

    def _save_directory_baseline(self, new_baseline: list[str]):
        """Saves the given baseline to the data file"""
        with open(self.data_file_path, "wb") as f:
            pickle.dump(new_baseline, f)
            logger.debug(f"Overwrote new directory baseline to {self.data_file_path}")

    def _compare_directories_lists(self, old_list: list[str], new_list: list[str]) -> list[str]:
        """Compares a baseline list of directories to a new list and returns all new directories"""
        new_directories = list(set(new_list).difference(old_list)) # everything in new that isn't in old
        return new_directories
