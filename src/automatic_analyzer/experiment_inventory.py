from __future__ import annotations
from abc import ABC
from pathlib import Path
import pickle
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
        If experiment does not already exist, it will be initialized with default parameters
        and any non-None given prop fields will be set.
        If experiment with given id already exists, any specified parameters will be overwritten while
        the rest will remain unchanged
        """
        if id not in self.experiments:
            default_props = ExperimentProperties.make_default()
            self.experiments[id] = Experiment(id=id, props=default_props)
        else:
            logger.debug(f"Experiment {id} already exists, replacing props")

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

    def __init__(
        self, data_file_path: Path, overrides: dict[str, Experiment] | None = None
    ) -> None:
        super().__init__(overrides)
        self.data_file_path = data_file_path

    def set(self, pattern: str, props: ExperimentProperties) -> None:
        """
        Add a new override with given Regex pattern and automatically saves to data file.
        Any experiments matching this pattern will be overriden with the provided experiment parameters.
        Note that any `None` prop fields will set the override to default props
        except the `overridden` field, which will be force set to True
        """
        props.overridden = True
        super().set(pattern, props)
        self._save_to_file()

    def set_exp(self, exp: Experiment):
        """
        Add given `Experiment` to override and automatically saves to data file.
        The ID of the experiment can be any valid Regex pattern.
        Note that any `None` prop fields will set the override to default props
        except the `overridden` field, which will be force set to True
        """
        exp.props.overridden = True
        super().set_exp(exp)
        # don't save here because set_exp calls set already

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

    def _save_to_file(self):
        """
        Saves the current override inventory to the a pickle file at the provided path.
        Note - this will overwrite any existing file at the path!
        """
        with open(self.data_file_path, "wb") as f:
            pickle.dump(self.experiments, f)
            logger.info("Saved override inventory to file")
            logger.debug(f"Saved {self.experiments} to {self.data_file_path}")

    @classmethod
    def load_from_file(cls, data_file_path: Path):
        """
        Loads an existing OverrideInventory from the pickle file at the provided path.
        Returns an OverrideInventory object
        """
        with open(data_file_path, "rb") as f:
            return cls(data_file_path, pickle.load(f))


class ExperimentInventory(ExperimentDict):
    """Main inventory of experiments in QMI data drive"""

    def __init__(self, override_inventory: OverrideInventory) -> None:
        super().__init__()
        self._override_inventory = override_inventory

    def set(self, id: str, props: ExperimentProperties) -> None:
        override_exp = self._override_inventory.get_override_exp(id)
        if override_exp is not None:
            logger.debug(f"Overriding experiment {id} with {override_exp.__repr__()}")
            props = override_exp.props

        super().set(id, props)
