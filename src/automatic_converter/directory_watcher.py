import os
from loguru import logger
from pathlib import Path

class ExperimentScanner:
    def __init__(self, scan_directory_target: str) -> None:
        self.scan_directory_target = scan_directory_target
        pass

    def scan_directory(self) -> list[str]:
        """Scans target directory and returns list of experiment IDs found in target"""
        directories = [Path(f.path).parts[-1] for f in os.scandir(self.scan_directory_target) if f.is_dir()]
        logger.debug(f"Scanned directories in watch_folder: {directories}")
        return directories

    def compare_exp_lists(self, old_list: list[str], new_list: list[str]) -> list[str]:
        """Compares a baseline list of experiments to a new list and returns all new experiments"""
        new_experiments = list(set(new_list).difference(old_list)) # everything in new that isn't in old
        return new_experiments

class DirectoryWatcher:
    def __init__(self, watch_directory: str, baseline_directories_list: list[str]|None) -> None:
        """Loads baseline from given data file path or scans and saves new baseline from given watch directory"""
        self.watch_directory = watch_directory
        if baseline_directories_list is not None:
            logger.info(f"Using existing baseline: {baseline_directories_list}")
            self.baseline_directories_list: list[str] = baseline_directories_list
        else:
            logger.info("Directories list file empty/not found, scanning new baseline")
            self.baseline_directories_list = self._scan_watch_directory()
    
    def find_new_directories(self) -> list[str]:
        """Refreshes directory baseline and returns any new directories that did not exist on the old baseline"""
        new_baseline = self._scan_watch_directory()
        new_directories = self._compare_directories_lists(self.baseline_directories_list, new_baseline)
        
        self.baseline_directories_list = new_baseline
        return new_directories
        
    def _scan_watch_directory(self) -> list[str]:
        """Scans the watch directory and returns new baseline"""
        directories = [f.path for f in os.scandir(self.watch_directory) if f.is_dir()]
        logger.debug(f"Scanned directories in watch_folder: {directories}")
        return directories

    def _compare_directories_lists(self, old_list: list[str], new_list: list[str]) -> list[str]:
        """Compares a baseline list of directories to a new list and returns all new directories"""
        new_directories = list(set(new_list).difference(old_list)) # everything in new that isn't in old
        return new_directories
