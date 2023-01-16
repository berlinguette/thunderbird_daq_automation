import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union

from data_converter.utilities.logging import get_conversion_logfile_path
from utilities.utilities.configuration.configuration import Config, ConfigSetup
from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)


class AbstractDataConverter(ABC):
    def __init__(
        self,
        experiment_source: Path,
        config: Config,
        config_setup: ConfigSetup,
        destination: Path
    ):
        self._experiment_source = experiment_source
        self._config = config
        self._config_setup = config_setup
        self._destination = destination

        self._logger = logging.getLogger('converter')
        self._logfile_path = get_conversion_logfile_path(
            self._experiment_source)
        setup_logger(self._logger, self._logfile_path)
        self._messenger = Messenger(self._logger)
        self._log_only_messenger = Messenger(self._logger, on_screen=False)
        self._screen_only_messenger = Messenger(self._logger, in_log=False)

    @property
    def experiment_root(self) -> Path:
        return self._experiment_source

    @property
    def messenger(self) -> Messenger:
        return self._messenger

    @abstractmethod
    def convert(self) -> bool:
        pass

    def _prepare_destinations(
        self, destinations: Union[Path, List[Path]]
    ):
        """Ensures that the destination paths exist, and are empty if needed

        Parameters
        ----------
        destination_path : Path | list[Path]
            Destination paths to prepare
        """
        if not isinstance(destinations, list):
            destinations = [destinations]
        for destination in destinations:
            # destinations must exist for converters to work properly
            if not destination.exists():
                self._log_only_messenger.debug(
                    f'Making destination {destination}')
                destination.mkdir()

    def _initial_messages(self):
        self._screen_only_messenger.info('')
        self._log_only_messenger.debug(
            f'Final configuration: {self._config}')

    def _finish_conversion(self):
        self._messenger.info(
            f"Conversion of {self._experiment_source} complete")
        self._screen_only_messenger.info('')
        cleanup_logger(self._logger)
