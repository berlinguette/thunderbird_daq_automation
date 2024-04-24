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

    def add(
        self,
        id: str,
        has_unconverted: bool | Literal["Error"] = False,
        has_converted: bool | Literal["Error"] = False,
        has_processed: bool | Literal["Error"] = False,
    ) -> bool:
        """
        Add a new `Experiment` to dict with given id.
        Returns True if add was successful and False if id is already in dict.
        """
        return self.add_exp(
            Experiment(
                id=id,
                has_unconverted=has_unconverted,
                has_converted=has_converted,
                has_processed=has_processed,
            )
        )

    def add_exp(self, exp: Experiment) -> bool:
        """
        Add given `Experiment` to dict.
        Returns True if succeeded or False if experiment already exists
        """
        if exp.id in self.experiments:
            logger.debug(f"Experiment {exp.id} already exists")
            return False
        else:
            self.experiments[exp.id] = exp
            logger.debug(f"Added experiment {exp.id}")
            return True

    def get(self, id: str) -> Experiment | None:
        return self.experiments.get(id)


class OverrideInventory(ExperimentDict):
    """
    Inventory of manual override values for experiments that will
    take precedence over values of actual experiments on disk
    """

    def __init__(self, overrides: dict[str, Experiment]) -> None:
        super().__init__(overrides)

    def add(
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
        return super().add(pattern, has_unconverted, has_converted, has_processed)

    def add_exp(self, exp: Experiment) -> bool:
        """
        Add given `Experiment` to override. The ID of the experiment can be any valid Regex pattern.
        Returns True if succeeded or False if experiment already exists
        """
        return super().add_exp(exp)

    def get(self, pattern: str) -> Experiment | None:
        return self.experiments.get(pattern)

    def get_all(self) -> list[Experiment]:
        logger.debug(f"All overrides: {self.experiments.values()}")
        return list(self.experiments.values())
    
    def should_override_exp(self, id: str) -> bool:
        """
        Returns True if given id matches an override pattern in the override inventory, and False otherewise
        """
        for override in self.experiments.values():
                if re.search(override.id, id) is not None:
                    return True
        return False


class ExperimentInventory(ExperimentDict):
    """Main inventory of experiments in QMI data drive"""

    def __init__(self, override_inventory: OverrideInventory) -> None:
        super().__init__()
        self._override_inventory = override_inventory

    def add_exp(self, exp: Experiment) -> bool:
        """
        Add given `Experiment` to inventory.
        If the experiment ID matches any override patterns,
        its parameters will be overwritten with the override experiment.
        Returns True if succeeded or False if experiment already exists
        """
        for pattern, override_exp in self._override_inventory.experiments.items():
            match = re.search(pattern, exp.id)
            if match is not None:
                new_overriden_exp = Experiment(
                    id=exp.id,
                    has_unconverted=override_exp.has_unconverted,
                    has_converted=override_exp.has_converted,
                    has_processed=override_exp.has_processed,
                )
                logger.info(
                    f"Overriding experiment {exp.id} with {new_overriden_exp.__repr__()}"
                )
                return super().add_exp(new_overriden_exp)
        return super().add_exp(exp)
