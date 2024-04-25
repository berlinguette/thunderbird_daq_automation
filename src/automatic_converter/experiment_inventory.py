from abc import ABC
from typing import Literal
from loguru import logger
from pydantic import BaseModel, Field
import re


class Experiment(BaseModel):
    """
    Represents an experiment in the QMI data drive.
    By default, experiments are marked as not present in all folders.
    For each folder, experiments are either present (valid mtime), not present (`None`), or malformed (`"Error"`)
    """

    id: str
    unconverted_mtime: float | Literal["Error"] | None = None
    converted_mtime: float | Literal["Error"] | None = None
    processed_mtime: float | Literal["Error"] | None = None

    # def __init__(
    #     self,
    #     id: str,
    #     has_unconverted: bool | Literal["Error"] = False,
    #     has_converted: bool | Literal["Error"] = False,
    #     has_processed: bool | Literal["Error"] = False,
    # ) -> None:
    #     self.id = id
    #     self.has_unconverted = has_unconverted
    #     self.has_converted = has_converted
    #     self.has_processed = has_processed

    # def __repr__(self) -> str:
    #     return (
    #         "Experiment(id=%r, has_unconverted=%r, has_converted=%r, has_processed=%r)"
    #         % (
    #             self.id,
    #             self.has_unconverted,
    #             self.has_converted,
    #             self.has_processed,
    #         )
    #     )

    # def to_dict(self) -> dict[str, Any]:
    #     return {
    #         "id": self.id,
    #         "has_unconverted": self.has_unconverted,
    #         "has_converted": self.has_converted,
    #         "has_processed": self.has_processed,
    #     }


class ExperimentDict(ABC):
    """
    Abstract base class for working with a dict of Experiments
    """

    def __init__(self, experiments: dict[str, Experiment] | None = None) -> None:
        self.experiments: dict[str, Experiment] = {}
        if experiments is not None:
            self.experiments = experiments

    def set(
        self,
        id: str,
        unconverted_mtime: float | Literal["Error"] | None = None,
        converted_mtime: float | Literal["Error"] | None = None,
        processed_mtime: float | Literal["Error"] | None = None,
    ) -> None:
        """
        Add given `Experiment` with given id to dict.
        If experiment with given id already exists, any specified parameters will be overwritten while
        the rest will remain unchanged
        """
        if id not in self.experiments:
            logger.debug(
                f"Experiment {id} does not exist, creating new default experiment"
            )
            self.experiments[id] = Experiment(id=id)
        if unconverted_mtime is not None:
            self.experiments[id].unconverted_mtime = unconverted_mtime
        if converted_mtime is not None:
            self.experiments[id].converted_mtime = converted_mtime
        if processed_mtime is not None:
            self.experiments[id].processed_mtime = processed_mtime
        logger.debug(f"Set experiment {id} to {self.experiments[id]}")

    def set_exp(self, exp: Experiment):
        """
        Add given `Experiment` to dict, or overwrite if experiment with given id already exists.
        """
        self.set(exp.id, exp.unconverted_mtime, exp.converted_mtime, exp.processed_mtime)

    def get(self, id: str) -> Experiment | None:
        return self.experiments.get(id)


class OverrideInventory(ExperimentDict):
    """
    Inventory of manual override values for experiments that will
    take precedence over values of actual experiments on disk
    """

    def __init__(self, overrides: dict[str, Experiment] | None = None) -> None:
        super().__init__(overrides)

    def set(
        self,
        pattern: str,
        unconverted_mtime: float | Literal["Error"] | None = None,
        converted_mtime: float | Literal["Error"] | None = None,
        processed_mtime: float | Literal["Error"] | None = None,
    ) -> None:
        """
        Add a new override with given Regex pattern.
        Any experiments matching this pattern will be overriden with the provided experiment parameters
        """
        super().set(pattern, unconverted_mtime, converted_mtime, processed_mtime)

    def set_exp(self, exp: Experiment) -> bool:
        """
        Add given `Experiment` to override. The ID of the experiment can be any valid Regex pattern.
        Returns True if succeeded or False if experiment already exists
        """
        return super().set_exp(exp)

    def get(self, pattern: str) -> Experiment | None:
        return self.experiments.get(pattern)

    def get_all(self) -> list[Experiment]:
        logger.debug(f"All overrides: {self.experiments.values()}")
        return list(self.experiments.values())

    def get_override_exp(self, id: str) -> Experiment | None:
        """
        Returns override experiment whose pattern matches given id, or None otherewise
        """
        for override in self.experiments.values():
            if re.search(override.id, id) is not None:
                return override
        return None


class ExperimentInventory(ExperimentDict):
    """Main inventory of experiments in QMI data drive"""

    def __init__(self, override_inventory: OverrideInventory) -> None:
        super().__init__()
        self._override_inventory = override_inventory

    def set(
        self,
        id: str,
        unconverted_mtime: float | Literal["Error"] | None = None,
        converted_mtime: float | Literal["Error"] | None = None,
        processed_mtime: float | Literal["Error"] | None = None,
    ) -> None:
        """
        Add given `Experiment` to inventory.
        If experiment with given id already exists, any specified parameters will be overwritten.
        If the experiment ID matches any override patterns,
        its parameters will instead be overwritten with the override experiment
        """
        override_exp = self._override_inventory.get_override_exp(id)
        if override_exp is not None:
            logger.info(f"Overriding experiment {id} with {override_exp.__repr__()}")
            unconverted_mtime = override_exp.unconverted_mtime
            converted_mtime = override_exp.converted_mtime
            processed_mtime = override_exp.processed_mtime

        super().set(id, unconverted_mtime, converted_mtime, processed_mtime)
