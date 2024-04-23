from typing import Any, Literal
from loguru import logger

class Experiment:
    """
    Represents an experiment in the QMI data drive.
    By default, experiments are marked as not present in all folders.
    For each folder, experiments are either not present (`False`), present (`True`), or malformed (`"Error"`)
    """

    def __init__(
        self,
        id: str,
        has_unconverted: bool | Literal["Error"] = False,
        has_converted: bool | Literal["Error"] = False,
        has_processed: bool | Literal["Error"] = False,
    ) -> None:
        self.id = id
        self.has_unconverted = has_unconverted
        self.has_converted = has_converted
        self.has_processed = has_processed

    def __repr__(self) -> str:
        return (
            "Experiment(id=%r, has_unconverted=%r, has_converted=%r, has_processed=%r)"
            % (
                self.id,
                self.has_unconverted,
                self.has_converted,
                self.has_processed,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "has_unconverted": self.has_unconverted,
            "has_converted": self.has_converted,
            "has_processed": self.has_processed,
        }


class ExperimentInventory:
    def __init__(self) -> None:
        self.experiments: dict[str, Experiment] = {}

    def add(
        self,
        id: str,
        has_unconverted: bool | Literal["Error"] = False,
        has_converted: bool | Literal["Error"] = False,
        has_processed: bool | Literal["Error"] = False,
    ) -> bool:
        """
        Add a new Experiment to inventory with given id.
        Returns True if add was successful and False if id is already in inventory.
        """
        return self.add_exp(
            Experiment(id, has_unconverted, has_converted, has_processed)
        )

    def add_exp(self, exp: Experiment) -> bool:
        """
        Add given `Experiment` to inventory.
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
