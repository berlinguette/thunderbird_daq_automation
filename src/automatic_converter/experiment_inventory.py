from __future__ import annotations
from abc import ABC
from typing import Literal
from loguru import logger
from pydantic import BaseModel
import re


class ExperimentProperties(BaseModel):
    """
    Represents properties of an experiment.
    All properties can be `None`, which is not a valid default value -
    it represents that we want to keep the old value that was there previously.
    An overridden experiment has had its actual values replaced by manual override values.
    mtimes with a value of -1 represent that the directory it does not exist
    """

    unconverted_mtime: float | Literal["Error"] | None = None
    converted_mtime: float | Literal["Error"] | None = None
    processed_mtime: float | Literal["Error"] | None = None
    overridden: bool | None = None

    def replace_props(self, new_props: ExperimentProperties):
        """
        Replace properties with new given ExperimentProperties.
        Any values in the new props that are `None` will be ignored, and the current value will be kept.
        """
        if new_props.unconverted_mtime is not None:
            self.unconverted_mtime = new_props.unconverted_mtime
        if new_props.converted_mtime is not None:
            self.converted_mtime = new_props.converted_mtime
        if new_props.processed_mtime is not None:
            self.processed_mtime = new_props.processed_mtime
        if new_props.overridden is not None:
            self.overridden = new_props.overridden

    @classmethod
    def make_default(cls) -> ExperimentProperties:
        """
        Returns a new ExperimentProperties with default values set.
        Experiment is marked as not present in unconverted, converted, and processed directories.
        Experiment is marked as not overridden
        """
        return cls(
            unconverted_mtime=-1,
            converted_mtime=-1,
            processed_mtime=-1,
            overridden=False,
        )

class Experiment(BaseModel):
    """
    Represents an experiment in the QMI data drive.
    By default, experiments are marked as not present in all folders.
    For each folder, experiments are either present (valid mtime), not present (`None`), or malformed (`"Error"`)
    """

    id: str
    props: ExperimentProperties

    class Config:
        # ExperimentProperties is an arbitrary class
        arbitrary_types_allowed = True


class ExperimentDict(ABC):
    """
    Abstract base class for working with a dict of Experiments
    """

    def __init__(self, experiments: dict[str, Experiment] | None = None) -> None:
        self.experiments: dict[str, Experiment] = {}
        if experiments is not None:
            self.experiments = experiments

    def set(self, id: str, props: ExperimentProperties) -> None:
        """
        Add given `Experiment` with given id to dict.
        If experiment with given id already exists, any specified parameters will be overwritten while
        the rest will remain unchanged
        """
        if id not in self.experiments:
            logger.debug(
                f"Experiment {id} does not exist, creating new default experiment"
            )
            exp_props = ExperimentProperties.make_default()
            exp_props.replace_props(props)
            self.experiments[id] = Experiment(id=id, props=exp_props)
        else:
            self.experiments[id].props.replace_props(props)
        logger.debug(f"Set experiment {id} to {self.experiments[id]}")

    def set_exp(self, exp: Experiment):
        """
        Add given `Experiment` to dict, or overwrite if experiment with given id already exists.
        """
        self.set(exp.id, exp.props)

    def get(self, id: str) -> Experiment | None:
        return self.experiments.get(id)


class OverrideInventory(ExperimentDict):
    """
    Inventory of manual override values for experiments that will
    take precedence over values of actual experiments on disk
    """

    def __init__(self, overrides: dict[str, Experiment] | None = None) -> None:
        super().__init__(overrides)

    def set(self, pattern: str, props: ExperimentProperties) -> None:
        """
        Add a new override with given Regex pattern.
        Any experiments matching this pattern will be overriden with the provided experiment parameters.
        Note that any given props with the `None` value will be ignored
        """
        super().set(pattern, props)

    def set_exp(self, exp: Experiment):
        """
        Add given `Experiment` to override. The ID of the experiment can be any valid Regex pattern.
        Note that any given props with the `None` value will be ignored
        """
        super().set_exp(exp)

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

    def set(self, id: str, props: ExperimentProperties) -> None:
        """
        Add given `Experiment` to inventory.
        If experiment with given id already exists, any specified props will be overwritten.
        If the experiment ID matches any override patterns,
        its props will instead be overwritten with the override experiment's props
        """
        override_exp = self._override_inventory.get_override_exp(id)
        if override_exp is not None:
            logger.info(f"Overriding experiment {id} with {override_exp.__repr__()}")
            props = override_exp.props

        super().set(id, props)
