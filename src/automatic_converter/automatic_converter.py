from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
)
import data_converter.data_converter as data_converter
from threading import Thread
from queue import SimpleQueue

class AutomaticConverter:
    in_progress_exp: str = ""

    def __init__(self, converted_data_dir) -> None:
        self.converted_data_dir = converted_data_dir
        self._config_setup = load_config_setup()
        self._config = get_configuration({}, self._config_setup, None)
        self._conversion_queue = SimpleQueue()

        self._converter_thread = Thread(target=self._converter)
        self._converter_thread.daemon = True
        self._converter_thread.start()

    def convert(self, exp_path: str):
        self._conversion_queue.put(exp_path)
    
    def status(self):
        return self.in_progress_exp

    def _converter(self):
        while True:
            exp_path = self._conversion_queue.get() # blocks until item available
            self.in_progress_exp = exp_path
            data_converter.convert_neutron_data(
                self._config,
                self._config_setup,
                sources=[exp_path],
                destination=self.converted_data_dir,
            )
            self.in_progress_exp = ""
            