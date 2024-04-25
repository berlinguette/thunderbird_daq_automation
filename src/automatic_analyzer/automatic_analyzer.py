from pathlib import Path
from loguru import logger
from pydantic import BaseModel
from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
)
import data_converter.data_converter as data_converter
from threading import Thread, Lock
from queue import Queue


class AnalysisParams(BaseModel):
    convert_unconverted: bool = True
    process_converted: bool = True


class Analysis(BaseModel):
    """
    Represents an analysis that we want to queue
    """

    id: str
    params: AnalysisParams


class AutomaticAnalyzer:
    in_progress_exp: Analysis|None = None
    in_progress_lock = Lock()

    def __init__(
        self,
        unconverted_data_dir: Path,
        converted_data_dir: Path,
        processed_data_dir: Path,
    ) -> None:
        self.unconverted_data_dir = unconverted_data_dir
        self.converted_data_dir = converted_data_dir
        self.processed_data_dir = processed_data_dir

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
        in_progress_exp = self.in_progress_exp
        self.in_progress_lock.release()
        return {
            "current": in_progress_exp.dict() if in_progress_exp is not None else None,
            "queued": [analysis.dict() for analysis in list(self._analysis_queue.queue)],
        }

    def _analyzer(self):
        while True:
            exp = self._analysis_queue.get()  # blocks until item available
            logger.info(f"Starting analysis of experiment {exp}")
            exp_path = Path(self.unconverted_data_dir, exp.id)
            self.in_progress_lock.acquire()
            self.in_progress_exp = exp
            self.in_progress_lock.release()

            if exp.params.convert_unconverted:
                logger.info(f"Converting experiment {exp.id}")
                data_converter.convert_neutron_data(
                    self._config,
                    self._config_setup,
                    sources=[exp_path],
                    destination=self.converted_data_dir,
                )
                logger.info(f"Finished converting experiment {exp.id}")
            self.in_progress_lock.acquire()
            self.in_progress_exp = None
            self.in_progress_lock.release()
