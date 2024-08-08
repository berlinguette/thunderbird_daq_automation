from pathlib import Path
import pickle
from pydantic import BaseModel, Field, validator
import re

from automatic_analyzer.analysis_step import BaseAnalysisStepProps
from automatic_analyzer.analysis_config import ANALYSIS_STEPS_LEN


class Override(BaseModel):
    """Overrides are used to manually override experiment props"""

    pattern: str
    analysis_step_overrides: list[BaseAnalysisStepProps | None]

    @validator("analysis_step_overrides")
    def proper_steps_len(cls, v):
        if len(v) != ANALYSIS_STEPS_LEN:
            raise ValueError("analysis_step_overrides list has invalid length")
        return v


class OverrideInventory:
    """
    Inventory of manual override values for experiments that will
    take precedence over values of actual experiments on disk
    """

    def __init__(
        self, data_file_path: Path, overrides: dict[str, Override] | None = None
    ) -> None:
        self._overrides: dict[str, Override] = {}
        if overrides is not None:
            self._overrides = overrides
        self._data_file_path = data_file_path

    def set(
        self, pattern: str, analysis_step_overrides: list[BaseAnalysisStepProps | None]
    ) -> None:
        """
        Add a new override with given Regex pattern and automatically saves to data file.
        Any experiments matching this pattern will be overriden with the provided experiment parameters.
        Note that any `None` prop fields will set the override to default props
        except the `overridden` field, which will be force set to True
        """
        if pattern not in self._overrides:
            self._overrides[pattern] = Override(
                pattern=pattern, analysis_step_overrides=analysis_step_overrides
            )
        else:
            self._overrides[pattern].analysis_step_overrides = analysis_step_overrides

        self._save_to_file()

    def set_exp(self, exp: Override):
        """
        Add given `Override` to override inventory and automatically saves to data file.
        The ID of the experiment can be any valid Regex pattern.
        Note that any `None` prop fields will set the override to default props
        except the `overridden` field, which will be force set to True
        """
        self.set(exp.pattern, exp.analysis_step_overrides)
        # don't save here because set_exp calls set already

    def get(self, pattern: str) -> Override | None:
        return self._overrides.get(pattern)

    def get_all(self) -> list[Override]:
        # logger.debug(f"All overrides: {self.overrides.values()}")
        return list(self._overrides.values())

    def delete(self, pattern: str):
        """
        Delete experiment with the given pattern, if it exists - otherwise do nothing.
        The data file will automatically be updated
        """
        self._overrides.pop(pattern, None)
        self._save_to_file()

    def get_override_exp(self, id: str) -> Override | None:
        """
        Returns override whose pattern matches given id, or None otherewise
        """
        for override in self._overrides.values():
            if re.search(override.pattern, id) is not None:
                return override
        return None

    def _save_to_file(self):
        """
        Saves the current override inventory to the a pickle file at the provided path.
        Note - this will overwrite any existing file at the path!
        """
        with open(self._data_file_path, "wb") as f:
            pickle.dump(self._overrides, f)
            # logger.info("Saved override inventory to file")
            # logger.debug(f"Saved {self.overrides} to {self.data_file_path}")

    @classmethod
    def load_from_file(cls, data_file_path: Path):
        """
        Loads an existing OverrideInventory from the pickle file at the provided path.
        Returns an OverrideInventory object
        """
        with open(data_file_path, "rb") as f:
            return cls(data_file_path, pickle.load(f))
