from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
)
import data_converter.data_converter as data_converter
from threading import Thread, Lock
from queue import Queue

class AutomaticAnalyzer:
    in_progress_exp: str = ""
    in_progress_lock = Lock()

    def __init__(self, converted_data_dir) -> None:
        self.converted_data_dir = converted_data_dir
        self._config_setup = load_config_setup()
        self._config = get_configuration({}, self._config_setup, None)
        self._conversion_queue = Queue()

        self._converter_thread = Thread(target=self._analyzer)
        self._converter_thread.daemon = True
        self._converter_thread.start()

    def analyze(self, exp_path: str):
        self._conversion_queue.put(exp_path)
    
    def status(self):
        self.in_progress_lock.acquire()
        in_progress_exp = self.in_progress_exp
        self.in_progress_lock.release()
        return {
            "current": in_progress_exp,
            "queued": [str(exp) for exp in list(self._conversion_queue.queue)]
        }

    def _analyzer(self):
        while True:
            exp_path = self._conversion_queue.get() # blocks until item available
            self.in_progress_lock.acquire()
            self.in_progress_exp = str(exp_path)
            self.in_progress_lock.release()
            data_converter.convert_neutron_data(
                self._config,
                self._config_setup,
                sources=[exp_path],
                destination=self.converted_data_dir,
            )
            self.in_progress_lock.acquire()
            self.in_progress_exp = ""
            self.in_progress_lock.release()
            