from abc import ABC
from typing import Literal
from loguru import logger
from pydantic import BaseModel
import re


class Experiment(BaseModel):
    """
    Represents an experiment in the QMI data drive.
    By default, experiments are marked as not present in all folders.
    For each folder, experiments are either not present (`False`), present (`True`), or malformed (`"Error"`)
    """

    id: str
    has_unconverted: bool | Literal["Error"] = False
    has_converted: bool | Literal["Error"] = False
    has_processed: bool | Literal["Error"] = False

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
        has_unconverted: bool | Literal["Error"] | None = None,
        has_converted: bool | Literal["Error"] | None = None,
        has_processed: bool | Literal["Error"] | None = None,
    ) -> bool:
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
        if has_unconverted is not None:
            self.experiments[id].has_unconverted = has_unconverted
        if has_converted is not None:
            self.experiments[id].has_converted = has_converted
        if has_processed is not None:
            self.experiments[id].has_processed = has_processed
        logger.debug(f"Set experiment {id} to {self.experiments[id]}")

    def set_exp(self, exp: Experiment):
        """
        Add given `Experiment` to dict, or overwrite if experiment with given id already exists.
        """
        self.set(exp.id, exp.has_unconverted, exp.has_converted, exp.has_processed)

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
        has_unconverted: bool | Literal["Error"] = False,
        has_converted: bool | Literal["Error"] = False,
        has_processed: bool | Literal["Error"] = False,
    ) -> bool:
        """
        Add a new override with given Regex pattern.
        Any experiments matching this pattern will be overriden with the provided experiment parameters.
        Returns True if add was successful and False if pattern is already in dict.
        """
        return super().set(pattern, has_unconverted, has_converted, has_processed)

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
        has_unconverted: bool | None | Literal["Error"] = None,
        has_converted: bool | None | Literal["Error"] = None,
        has_processed: bool | None | Literal["Error"] = None,
    ) -> bool:
        """
        Add given `Experiment` to inventory.
        If experiment with given id already exists, any specified parameters will be overwritten.
        If the experiment ID matches any override patterns,
        its parameters will instead be overwritten with the override experiment
        """
        override_exp = self._override_inventory.get_override_exp(id)
        if override_exp is not None:
            logger.info(f"Overriding experiment {id} with {override_exp.__repr__()}")
            has_unconverted = override_exp.has_unconverted
            has_converted = override_exp.has_converted
            has_processed = override_exp.has_processed

        super().set(id, has_unconverted, has_converted, has_processed)