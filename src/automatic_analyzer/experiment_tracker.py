import re
from automatic_analyzer.experiment_inventory import (
    Experiment,
    ExperimentInventory,
    ExperimentProperties,
    OverrideInventory,
)
from pathlib import Path
from loguru import logger
import os


class ExperimentTracker:
    """
    Tracks inventory of all experiments in QMI data drive
    """

    def __init__(
        self,
        unconverted_data_dir: Path,
        converted_data_dir: Path,
        processed_data_dir: Path,
        overrides: OverrideInventory,
    ) -> None:
        """Initializes new experiment inventory and establishes directory baseline"""
        self._unconverted_data_dir = unconverted_data_dir
        self._converted_data_dir = converted_data_dir
        self._processed_data_dir = processed_data_dir
        self._overrides = overrides

        self.experiments = ExperimentInventory(overrides)
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
        logger.debug(f"New inventory: {self.experiments.experiments}")

    def get_all_experiments(self) -> list[Experiment]:
        """Get all experiments in internal inventory"""
        logger.debug(f"All experiments: {self.experiments.experiments.values()}")
        return list(self.experiments.experiments.values())

    def get_all_to_convert(self) -> list[Experiment]:
        """Get all experiments that are in unconverted directory but not converted"""
        to_convert = []
        for exp in self.experiments.experiments.values():
            if exp.props.unconverted_mtime != -1 and exp.props.converted_mtime == -1:
                to_convert.append(exp)
        logger.debug(f"All to-be-converted experiments: {to_convert}")
        return to_convert

    def get_all_to_process(self) -> list[Experiment]:
        """Get all experiments that are in converted directory but not processed"""
        to_process = []
        for exp in self.experiments.experiments.values():
            if exp.props.converted_mtime != -1 and exp.props.processed_mtime == -1:
                to_process.append(exp)
        logger.debug(f"All to-be-processed experiments: {to_process}")
        return to_process

    def get_all_to_analyze(self) -> list[Experiment]:
        """Get all experiments that are in unconverted directory but not converted or processed"""
        to_analyze = []
        for exp in self.experiments.experiments.values():
            if exp.props.unconverted_mtime != -1 and (
                exp.props.converted_mtime == -1 or exp.props.processed_mtime == -1
            ):
                to_analyze.append(exp)
        logger.debug(f"All to-be-analyzed experiments: {to_analyze}")
        return to_analyze

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
        # Clear all unconverted statuses at beginning except overridden experiments
        for exp in self.experiments.experiments.values():
            if not exp.props.overridden:
                exp.props.unconverted_mtime = -1
            else:
                logger.debug(f"Skip clearing overridden experiment {exp.id}")

        unconverted_exps = self._scan_directory(self._unconverted_data_dir)
        logger.info(f"Found unconverted experiments: {unconverted_exps}")
        for id, mtime in unconverted_exps:
            self.experiments.set(id, ExperimentProperties(unconverted_mtime=mtime, overridden=False))

    def _refresh_converted(self):
        """
        Rescans converted data directory and adds all found experiments to inventory,
        or marks presence of converted experiment if already exists.
        For each found experiment, the `conversion.log` file in the directory is also verified for errors,
        and the experiment is marked as `"Error"` if errors are found.
        """
        # Clear all converted statuses at beginning except overridden experiments
        for exp in self.experiments.experiments.values():
            if not exp.props.overridden:
                exp.props.converted_mtime = -1
            else:
                logger.debug(f"Skip clearing overridden experiment {exp.id}")
        converted_exps = self._scan_directory(self._converted_data_dir)
        logger.info(f"Found converted experiments: {converted_exps}")
        for id, mtime in converted_exps:
            exp_mtime = mtime
            try:
                exp_log_path = Path(self._converted_data_dir, id, "conversion.log")
                with open(exp_log_path, "r") as f:
                    contents = f.read()
                    if (
                        "ERROR" in contents
                        or re.search(f"Conversion of .*{id} complete", contents) is None
                    ):
                        logger.warning(
                            f"Experiment {id} could be malformed, check conversion.log"
                        )
                        exp_mtime = "Error"
            except FileNotFoundError:
                logger.warning(f"No conversion.log found for experiment {id}")
                exp_mtime = "Error"

            self.experiments.set(id, ExperimentProperties(converted_mtime=exp_mtime, overridden=False))

    def _refresh_processed(self):
        """
        Rescans processed data directory and adds all found experiments to inventory,
        or marks presence of processed experiment if already exists
        """
        # Clear all processed statuses at beginning except overridden experiments
        for exp in self.experiments.experiments.values():
            if not exp.props.overridden:
                exp.props.processed_mtime = -1
            else:
                logger.debug(f"Skip clearing overridden experiment {exp.id}")
        processed_exps = self._scan_directory(self._processed_data_dir)
        logger.info(f"Found processed experiments: {processed_exps}")
        for id, mtime in processed_exps:
            self.experiments.set(id, ExperimentProperties(processed_mtime=mtime, overridden=False))

    def _scan_directory(self, target_dir: Path) -> list[tuple[str, float]]:
        """Scans target directory and returns a list of pairs of experiment IDs found in target and their mtimes"""
        directories = [
            (f.parts[-1], f.lstat().st_mtime*1000)
            for f in target_dir.iterdir()
            if f.is_dir()
        ]
        logger.debug(f"Scanned directories in {target_dir}: {directories}")
        return directories
