import copy
from pathlib import Path
import subprocess
from typing import Literal
from loguru import logger
from pydantic import BaseModel
from automatic_analyzer.experiment_inventory import Experiment
from automatic_analyzer.experiment_tracker import ExperimentTracker
from utilities.utilities.configuration.configuration import (
    Config,
    ConfigSetup,
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


class AnalysisRequestParams(AnalysisParams):
    """
    Parameters in an analysis request from the endpoint.
    The `pattern` attribute is used to determine which analyses should be done.
    """

    pattern: str | None = None


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
    """
    Handles analysis of experiments. The main class instance maintains a queue of Analyses that is shared
    with the analyzer thread. Any new analyses are added onto the queue, and the analyzer thread will
    run them in order
    """

    # These could probably be instance fields instead of class fields?
    in_progress_analysis: Analysis | None = None
    in_progress_lock = Lock()

    def __init__(
        self,
        config_setup: ConfigSetup,
        config: Config,
        exp_tracker: ExperimentTracker,
        psd_python_binary_path: Path,
        psd_program_path: Path,
    ) -> None:
        """
        Sets up a new AutomaticAnalyzer.
        `psd_python_binary_path` is the path to the python binary that can run the PSD analysis script -
        it is likely located inside a `venv/Scripts` or `venv/bin` folder.
        `psd_program_path` is the path to the actual PSD analysis script.
        `config_setup` and `config` are passed on to the data_analyzer module
        """
        self.exp_tracker = exp_tracker
        self.psd_python_path = psd_python_binary_path
        self.psd_program_path = psd_program_path

        self._config_setup = config_setup
        self._config = config

        self._analysis_queue: "Queue[Analysis]" = Queue()
        self._converter_thread = Thread(target=self._analyzer)
        self._converter_thread.daemon = True
        self._converter_thread.start()

    def analyze(self, analysis: Analysis):
        """Adds given analysis to the queue, where it will be popped off and processed by the analyzer thread"""
        self._analysis_queue.put(analysis)
        logger.info(f"Added experiment {analysis} to analysis queue")

    def status(self):
        """
        Gets the latest analysis status from the analyzer thread,
        including the currently-running analysis and any queued analyses
        """
        with self.in_progress_lock:
            in_progress_analysis = self.in_progress_analysis
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
        """
        Main analyzer function. This should be run as a separate thread that is started when
        the AutomaticAnalyzer class is instantiated.
        The function blocks until an analysis is available in the shared queue, at which point it will
        try to convert/process the given experiments.
        """
        while True:
            current_analysis = self._analysis_queue.get()  # blocks until item available
            logger.info(f"Starting analysis of experiment {current_analysis.exp}")
            logger.debug(f"Analyzing {current_analysis}")
            with self.in_progress_lock:
                self.in_progress_analysis = copy.deepcopy(current_analysis)

            self._try_convert(current_analysis)
            self.exp_tracker.refresh_all()
            self._try_process(current_analysis)

            logger.info(f"Analysis of {current_analysis.exp} done")
            with self.in_progress_lock:
                self.in_progress_analysis = None

    def _try_convert(self, current_analysis: Analysis):
        """
        Tries to convert the experiment pattern specified in the current anlysis.
        By default, conversion will not be run if the unconverted files do not exist or if converted files already exist.
        However, if the force param is True then the conversion will be run regardless.
        """
        if not current_analysis.params.convert_unconverted:
            logger.info(
                f"'convert_unconverted' is False for current analysis of {current_analysis.exp.id}, skipping conversion"
            )
            return

        exp_path = Path(self.exp_tracker._unconverted_data_dir, current_analysis.exp.id)
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
            with self.in_progress_lock:
                if self.in_progress_analysis:
                    self.in_progress_analysis.stage = "convert"

            data_converter.convert_neutron_data(
                self._config,
                self._config_setup,
                sources=[exp_path],
                destination=self.exp_tracker._converted_data_dir,
            )
            logger.info(f"Finished converting experiment {exp}")

    def _try_process(self, current_analysis: Analysis):
        """
        Tries to process the experiment pattern specified in the current anlysis.
        By default, processing will not be run if the converted files do not exist or if processed files already exist.
        However, if the force param is True then the processing will be run regardless.
        """
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
            with self.in_progress_lock:
                if self.in_progress_analysis:
                    self.in_progress_analysis.stage = "process"

            program_input = f"{exp.id.split('-', maxsplit=1)[1]}\n\n\n\n\n\n\n\n"
            logger.debug(
                f"Running {self.psd_python_path} {self.psd_program_path} with input {program_input}"
            )
            output = subprocess.run(
                [self.psd_python_path, self.psd_program_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                input=program_input,
            )
            logger.info(f"Program output: {output.stdout}")
            logger.info(f"Finished processing experiment {exp}")
