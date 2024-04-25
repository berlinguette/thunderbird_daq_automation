import copy
from pathlib import Path
import subprocess
from typing import Literal
from loguru import logger
from pydantic import BaseModel
from automatic_analyzer.experiment_inventory import Experiment
from automatic_analyzer.experiment_tracker import ExperimentTracker
from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
)
import data_converter.data_converter as data_converter
from threading import Thread, Lock
from queue import Queue


class AnalysisParams(BaseModel):
    """
    Parameters for analyzing an experiment.
    Set `force` to `True` to to run analyses regardless of whether there are already existing files
    """

    convert_unconverted: bool = True
    process_converted: bool = True
    force: bool = False


class Analysis(BaseModel):
    """
    Represents an analysis that we want to queue.
    `cancelled` should not be set manually when creating this object -
    it is used by the Analyzer to mark cancelled analyses
    """

    exp: Experiment
    params: AnalysisParams
    stage: Literal["convert"] | Literal["process"] = "convert"
    cancelled: bool = False


class AutomaticAnalyzer:
    in_progress_analysis: Analysis | None = None
    in_progress_lock = Lock()

    def __init__(
        self,
        exp_tracker: ExperimentTracker,
        unconverted_data_dir: Path,
        converted_data_dir: Path,
        processed_data_dir: Path,
        psd_python_binary_path: Path,
        psd_program_path: Path,
    ) -> None:
        self.exp_tracker = exp_tracker
        self.unconverted_data_dir = unconverted_data_dir
        self.converted_data_dir = converted_data_dir
        self.processed_data_dir = processed_data_dir
        self.psd_python_path = psd_python_binary_path
        self.psd_program_path = psd_program_path

        self._config_setup = load_config_setup()
        self._config = get_configuration({}, self._config_setup, None)

        self._analysis_queue: "Queue[Analysis]" = Queue()
        self._converter_thread = Thread(target=self._analyzer)
        self._converter_thread.daemon = True
        self._converter_thread.start()

    def analyze(self, analysis: Analysis):
        self._analysis_queue.put(analysis)
        logger.info(f"Added experiment {analysis} to analysis queue")

    def status(self):
        self.in_progress_lock.acquire()
        in_progress_analysis = self.in_progress_analysis
        self.in_progress_lock.release()
        return {
            "current": in_progress_analysis.dict()
            if in_progress_analysis is not None
            else None,
            "queued": [
                analysis.dict() for analysis in list(self._analysis_queue.queue)
            ],
        }

    #############################
    # Analyzer thread functions #
    #############################

    def _analyzer(self):
        while True:
            current_analysis = self._analysis_queue.get()  # blocks until item available
            logger.info(f"Starting analysis of experiment {current_analysis.exp}")
            logger.debug(f"Analyzing {current_analysis}")
            self.in_progress_lock.acquire()
            self.in_progress_analysis = copy.deepcopy(current_analysis)
            self.in_progress_lock.release()

            self._try_convert(current_analysis)
            self.exp_tracker.refresh_all()
            self._try_process(current_analysis)

            logger.info(f"Analysis of {current_analysis.exp} done")
            self.in_progress_lock.acquire()
            self.in_progress_analysis = None
            self.in_progress_lock.release()

    def _try_convert(self, current_analysis: Analysis):
        if not current_analysis.params.convert_unconverted:
            logger.info(
                f"'convert_unconverted' is False for current analysis of {current_analysis.exp.id}, skipping conversion"
            )
            return

        exp_path = Path(self.unconverted_data_dir, current_analysis.exp.id)
        exp = current_analysis.exp
        run_conversion = True
        if exp.props.unconverted_mtime == -1:
            run_conversion = False
            logger.warning(f"Unconverted files for {exp.id} do not exist")
        if exp.props.converted_mtime != -1:
            run_conversion = False
            logger.warning(f"Converted files for {exp.id} already exist")
        if current_analysis.params.force:
            run_conversion = True
            logger.warning(f"Force running conversion script for {exp.id}")

        if run_conversion:
            logger.info(f"Converting experiment {exp}")
            self.in_progress_lock.acquire()
            self.in_progress_analysis.stage = "convert"
            self.in_progress_lock.release()

            data_converter.convert_neutron_data(
                self._config,
                self._config_setup,
                sources=[exp_path],
                destination=self.converted_data_dir,
            )
            logger.info(f"Finished converting experiment {exp}")

    def _try_process(self, current_analysis: Analysis):
        if not current_analysis.params.process_converted:
            logger.info(
                f"'process_converted' is False for current analysis of {current_analysis.exp.id}, skipping processing"
            )
            return

        exp = current_analysis.exp
        run_processing = True
        if exp.props.converted_mtime == -1:
            run_processing = False
            logger.warning(f"Converted files for {exp.id} do not exist")
        if exp.props.processed_mtime != -1:
            run_processing = False
            logger.warning(f"Processed files for {exp.id} already exist")
        if current_analysis.params.force:
            run_processing = True
            logger.warning(f"Force running processing script for {exp.id}")

        if run_processing:
            logger.info(f"Processing experiment {exp}")
            self.in_progress_lock.acquire()
            self.in_progress_analysis.stage = "process"
            self.in_progress_lock.release()

            program_input = f"{exp.id.split('-')[1]}\n\n\n\n\n\n\n"
            logger.debug(f"Running {self.psd_python_path} {self.psd_program_path} with input {program_input}")
            output = subprocess.run(
                [self.psd_python_path, self.psd_program_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                input=program_input
            )
            logger.debug(f"Program output: {output.stdout}")
            logger.info(f"Finished processing experiment {exp}")

