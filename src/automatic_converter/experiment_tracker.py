from automatic_converter.directory_watcher import ExperimentScanner
from automatic_converter.experiment_inventory import Experiment, ExperimentInventory
from pathlib import Path
from loguru import logger

class ExperimentTracker:
    def __init__(
        self,
        unconverted_data_dir: str,
        converted_data_dir: str,
        processed_data_dir: str,
    ) -> None:
        """Initializes new experiment inventory and establishes directory baseline"""
        self._unconverted_data_dir = unconverted_data_dir
        self._converted_data_dir = converted_data_dir
        self._processed_data_dir = processed_data_dir
        self._unconverted_data_scanner = ExperimentScanner(unconverted_data_dir)
        self._converted_data_scanner = ExperimentScanner(converted_data_dir)
        self._processed_data_scanner = ExperimentScanner(processed_data_dir)
        # self._unconverted_data_watcher = DirectoryWatcher(unconverted_data_dir)

        self.experiments = ExperimentInventory()
        self.refresh_all()

    def refresh_all(self):
        """
        Rescans the unconverted, converted, and processed data directories
        and marks presence of the experiments in all directories
        """
        self._refresh_unconverted()
        self._refresh_converted()
        self._refresh_processed()
        logger.info("Refreshed inventory for all directories")

    def get_all_experiments(self) -> list[Experiment]:
        """Get all experiments in internal inventory"""
        logger.debug(f"All experiments: {self.experiments.experiments.values()}")
        return list(self.experiments.experiments.values())

    def get_all_to_convert(self) -> list[Experiment]:
        """Get all experiments that are in unconverted directory but not converted"""
        to_convert = []
        for exp in self.experiments.experiments.values():
            if exp.has_unconverted and not exp.has_converted:
                to_convert.append(exp)
        logger.debug(f"All to-be-converted experiments: {to_convert}")
        return to_convert

    def get_all_to_process(self) -> list[Experiment]:
        """Get all experiments that are in converted directory but not processed"""
        to_process = []
        for exp in self.experiments.experiments.values():
            if exp.has_converted and not exp.has_processed:
                to_process.append(exp)
        logger.debug(f"All to-be-processed experiments: {to_process}")
        return to_process

    # def get_all_unconverted(self) -> list[Experiment]:
    #     """Get all experiments that are present in unconverted directory"""
    #     unconverted = []
    #     for exp in self.experiments.experiments.values():
    #         if exp.has_unconverted:
    #             unconverted.append(exp)
    #     return unconverted

    # def get_all_converted(self) -> list[Experiment]:
    #     """Get all experiments that are present in converted directory"""
    #     converted = []
    #     for exp in self.experiments.experiments.values():
    #         if exp.has_converted:
    #             converted.append(exp)
    #     return converted

    # def get_all_processed(self) -> list[Experiment]:
    #     """Get all experiments that are present in processed directory"""
    #     processed = []
    #     for exp in self.experiments.experiments.values():
    #         if exp.has_processed:
    #             processed.append(exp)
    #     return processed

    def _refresh_unconverted(self):
        """
        Rescans unconverted data directory and adds all found experiments to inventory,
        or marks presence of unconverted experiment if already exists
        """
        unconverted_exps = self._unconverted_data_scanner.scan_directory()
        logger.info(f"Found unconverted experiments: {unconverted_exps}")
        for id in unconverted_exps:
            if not self.experiments.add(id, has_unconverted=True):
                # if experiment already in inventory
                self.experiments.get(id).has_unconverted = True

    def _refresh_converted(self):
        """
        Rescans converted data directory and adds all found experiments to inventory,
        or marks presence of converted experiment if already exists.
        For each found experiment, the `conversion.log` file in the directory is also verified for errors,
        and the experiment is marked as `"Error"` if errors are found.
        """
        converted_exps = self._converted_data_scanner.scan_directory()
        logger.info(f"Found converted experiments: {converted_exps}")
        for id in converted_exps:
            exp_status = True
            try:
                exp_log_path = Path(self._converted_data_dir, id, "conversion.log")
                with open(exp_log_path, "r") as f:
                    if "ERROR" in f.read():
                        logger.warning(
                            f"Experiment {id} could be malformed, check conversion.log"
                        )
                        exp_status = "Error"
            except FileNotFoundError:
                logger.warning(f"No conversion.log found for experiment {id}")
                exp_status = "Error"

            if not self.experiments.add(id, has_converted=exp_status):
                # if experiment already in inventory
                self.experiments.get(id).has_converted = exp_status

    def _refresh_processed(self):
        """
        Rescans processed data directory and adds all found experiments to inventory,
        or marks presence of processed experiment if already exists
        """
        processed_exps = self._processed_data_scanner.scan_directory()
        logger.info(f"Found processed experiments: {processed_exps}")
        for id in processed_exps:
            if not self.experiments.add(id, has_processed=True):
                # if experiment already in inventory
                self.experiments.get(id).has_processed = True
