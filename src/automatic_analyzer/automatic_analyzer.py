import copy
from queue import Queue
from threading import Lock, Thread
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel, validator

from automatic_analyzer.analysis_config import ANALYSIS_STEPS_LEN
from automatic_analyzer.analysis_step import AnalysisStep
from automatic_analyzer.experiment_tracker import Experiment, ExperimentTracker

tracer = trace.get_tracer("automatic_analyzer_backend.automatic_analyzer")


class AnalysisParams(BaseModel):
    """
    Parameters for analyzing an experiment.

    :param steps_to_analyze: List of bools representing whether the analysis step at that index should be performed -
        the length should be one less than number of steps since the last step cannot be analyzed
    """

    steps_to_analyze: list[bool]

    @validator("steps_to_analyze")
    def proper_steps_len(cls, v):
        # IMPORTANT - we want a length of steps - 1 because the last step cannot be analyzed
        if len(v) != ANALYSIS_STEPS_LEN - 1:
            raise ValueError("steps_to_analyze list has invalid length")
        return v


class AnalysisRequestParams(AnalysisParams):
    pattern: str | None = None


class Analysis(BaseModel):
    """
    Represents an analysis that we want to queue.
    `cancelled` should not be set manually when creating this object -
    it is used by the Analyzer to mark cancelled analyses
    """

    exp: Experiment
    params: AnalysisParams
    current_step: int = 0
    cancelled: bool = False
    trace_context: dict[str, str] | None = None


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
        self, exp_tracker: ExperimentTracker, analysis_steps: list[AnalysisStep]
    ) -> None:
        """
        Sets up a new AutomaticAnalyzer.
        """
        self._exp_tracker = exp_tracker
        self._analysis_steps = analysis_steps

        self._analysis_queue: "Queue[Analysis]" = Queue()
        self._converter_thread = Thread(target=self._analyzer)
        self._converter_thread.daemon = True
        self._converter_thread.start()

    def analyze(self, analysis: Analysis):
        """Adds given analysis to the queue, where it will be popped off and processed by the analyzer thread"""
        # Write the current context into the carrier
        carrier: dict[str, str] = {}
        TraceContextTextMapPropagator().inject(carrier)
        analysis.trace_context = carrier

        with tracer.start_as_current_span("queue_analysis") as span:
            span.set_attribute("id", analysis.exp.id)
            self._analysis_queue.put(analysis)
            # logger.info(f"Added experiment {analysis.exp.id} to analysis queue")
            # logger.debug(f"Analysis params: {analysis}")

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
            ctx = TraceContextTextMapPropagator().extract(
                carrier=current_analysis.trace_context
            )
            with tracer.start_as_current_span("start_analysis", context=ctx) as span:
                span.set_attributes(
                    {
                        "id": current_analysis.exp.id,
                        # "convert_unconverted": current_analysis.params.convert_unconverted,
                        # "process_converted": current_analysis.params.process_converted,
                        # "force": current_analysis.params.force,
                    }
                )

                # logger.info(
                #     f"Starting analysis of experiment {current_analysis.exp.id}"
                # )
                # logger.debug(f"Analyzing {current_analysis}")
                with self.in_progress_lock:
                    self.in_progress_analysis = copy.deepcopy(current_analysis)

                self._exp_tracker.refresh_inventory()
                # Last step doesn't require analysis because it's the final state
                for i, step in enumerate(self._analysis_steps[:-1]):
                    if current_analysis.params.steps_to_analyze[i]:
                        self._exp_tracker.refresh_inventory()
                        self._analyze_step(current_analysis.exp, i)

                logger.info(f"Analysis of experiment {current_analysis.exp.id} done")
                with self.in_progress_lock:
                    self.in_progress_analysis = None

    def _analyze_step(self, experiment: Experiment, analysis_step_index: int):
        if experiment.analysis_step_props[analysis_step_index + 1].mtime_present():
            logger.debug(
                f"Experiment {experiment.id} already exists in step {analysis_step_index}, skipping"
            )
            return
        self._analysis_steps[analysis_step_index].analyze(experiment)
