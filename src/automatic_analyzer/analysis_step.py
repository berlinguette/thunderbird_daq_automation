from __future__ import annotations
from abc import ABC
import re
from loguru import logger
from opentelemetry import trace
from pathlib import Path
from pydantic import BaseModel
from typing import Generator, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from automatic_analyzer.experiment import Experiment

from data_converter import data_converter
from utilities.utilities.configuration.configuration import Config, ConfigSetup


tracer = trace.get_tracer("automatic_analyzer_backend.analysis_step")


class BaseAnalysisStepProps(BaseModel):
    """Base props about an analysis step - direct properties of the step"""

    mtime: float | Literal["Error"]

    def mtime_present(self):
        return self.mtime != "Error" and self.mtime > -1


class AnalysisStepProps(BaseAnalysisStepProps):
    """Props used for an analysis - contains additional metadata on top of base props"""

    overridden: bool = False

    @classmethod
    def make_from_base(
        cls, base_props: BaseAnalysisStepProps, overridden: bool = False
    ):
        return cls(mtime=base_props.mtime, overridden=overridden)


class AnalysisStep(ABC):
    """Represents a single analysis step of the data automation pipeline"""

    def __init__(self, name: str) -> None:
        self.name = name

    def check_experiments(
        self,
    ) -> Generator[tuple[str, BaseAnalysisStepProps], None, None]:
        """
        Returns a generator that yields pairs of experiment IDs
        found in target and their props
        """
        ...

    def analyze(self, exp: Experiment): ...

    def _scan_directory(
        self, target_dir: Path
    ) -> Generator[tuple[str, float], None, None]:
        """
        Scans target directory and returns a generator that yields
        pairs of experiment IDs found in target and their mtimes
        """
        directories = (
            (f.parts[-1], f.lstat().st_mtime * 1000)
            for f in target_dir.iterdir()
            if f.is_dir()
        )
        # logger.debug(f"Scanned directories in {target_dir}: {directories}")
        return directories


class UnconvertedAnalysisStep(AnalysisStep):
    def __init__(
        self,
        name: str,
        unconverted_path: Path,
        converted_path: Path,
        config_setup: ConfigSetup,
        config: Config,
    ) -> None:
        """
        `config_setup` and `config` are passed on to the data_analyzer module
        """
        super().__init__(name)
        self._unconverted_path = unconverted_path
        self._converted_path = converted_path
        self._config_setup = config_setup
        self._config = config

    def check_experiments(
        self,
    ) -> Generator[tuple[str, BaseAnalysisStepProps], None, None]:
        for id, mtime in self._scan_directory(self._unconverted_path):
            exp_folder_path = Path(self._unconverted_path, id)
            if len(list(exp_folder_path.glob("run.info"))) == 0:
                yield (id, BaseAnalysisStepProps(mtime="Error"))
            else:
                yield (id, BaseAnalysisStepProps(mtime=mtime))

    def analyze(self, exp: Experiment):
        exp_path = Path(self._unconverted_path, exp.id)
        with tracer.start_as_current_span("conversion_script"):
            data_converter.convert_neutron_data(
                self._config,
                self._config_setup,
                sources=[exp_path],
                destination=self._converted_path,
            )
            logger.info(f"Finished converting experiment {exp.id}")


class ConvertedAnalysisStep(AnalysisStep):
    def __init__(self, name: str, directory_path: Path) -> None:
        super().__init__(name)
        self._directory_path = directory_path

    def check_experiments(self) -> Generator[tuple[str, BaseAnalysisStepProps], None, None]:
        for id, mtime in self._scan_directory(self._directory_path):
            try:
                exp_log_path = Path(self._directory_path, id, "conversion.log")
                with open(exp_log_path, "r") as f:
                    contents = f.read()
                    if (
                        "error" in contents.lower()
                        or re.search(f"Conversion of .*{id} complete", contents) is None
                    ):
                        # logger.warning(
                        #     f"Experiment {id} could be malformed, check conversion.log"
                        # )
                        yield (id, BaseAnalysisStepProps(mtime="Error"))
                    else:
                        yield (id, BaseAnalysisStepProps(mtime=mtime))
            except FileNotFoundError:
                # logger.warning(f"No conversion.log found for experiment {id}")
                yield (id, BaseAnalysisStepProps(mtime="Error"))

    def analyze(self, exp: Experiment):
        # Final step
        return
