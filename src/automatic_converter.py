from pydantic import BaseModel, ValidationError
from automatic_converter.experiment_inventory import Experiment, OverrideInventory
from automatic_converter.experiment_tracker import ExperimentTracker
from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import (
    get_configuration,
    Config,
    ConfigSetup,
)
import data_converter.data_converter as data_converter
from automatic_converter.directory_watcher import DirectoryWatcher
from pathlib import Path
import pickle
from loguru import logger
from flask import Flask, request
import sys
# import logging

logger.remove()
logger.add(sys.stderr, level="INFO")
# logging.basicConfig(level=logging.DEBUG)

# neutron_data_path = "/mnt/qmi-share/Neutron Data/"
neutron_data_path = "/mnt/qmi-share/daniel_test_data"

unconverted_data_dir = Path(neutron_data_path, "1-Unconverted_Data")
converted_data_dir = Path(neutron_data_path, "2-Converted_Data")
processed_data_dir = Path(neutron_data_path, "3-Output")
# watch_folder = "Q:/Neutron Data/1-Unconverted_Data"
# target_folder = "Q:/Neutron Data/2-Converted_Data"

package_dir = Path(__file__).parent.absolute()
directories_list_file = Path(package_dir, "../data/directories.pkl")

class ConvertRequest(BaseModel):
    convert_unconverted: bool = True
    process_converted: bool = True


def initialize_default_data_converter() -> tuple[Config, ConfigSetup]:
    config_setup = load_config_setup()
    config = get_configuration({}, config_setup, None)
    return config, config_setup


def create_app():
    app = Flask(__name__)
    config, config_setup = initialize_default_data_converter()
    baseline_directories_list: list[str] | None = None
    try:
        with open(directories_list_file, "rb") as f:
            baseline_directories_list = pickle.load(f)
    except FileNotFoundError:
        pass

    dir_watcher = DirectoryWatcher(unconverted_data_dir, baseline_directories_list)
    overrides = OverrideInventory(
        {
            "ID-(338|350|FAKE.*)": Experiment(
                id="ID-(338|350|FAKE.*)",
                has_unconverted=True,
                has_converted=True,
                has_processed=True,
            )
        }
    )
    exp_tracker = ExperimentTracker(
        unconverted_data_dir, converted_data_dir, processed_data_dir, overrides
    )

    @app.get("/inventory")
    def get_inventory():
        exp_filter = request.args.get("filter", "all")
        get_exp_mapping = {
            "all": exp_tracker.get_all_experiments,
            "to_be_converted": exp_tracker.get_all_to_convert,
            "to_be_processed": exp_tracker.get_all_to_process,
        }
        if exp_filter not in get_exp_mapping:
            return "Invalid experiment filter", 400
        exp_tracker.refresh_all()
        return [exp.dict() for exp in get_exp_mapping[exp_filter]()]

    @app.get("/overrides")
    def get_overrides():
        return [exp.dict() for exp in overrides.get_all()]

    @app.post("/overrides")
    def new_override():
        if request.is_json:
            body = request.json
            try:
                exp = Experiment.parse_obj(body)
                if overrides.add_exp(exp):
                    return "", 201
                else:
                    return f"Experiment ID {exp.id} already exists", 409
            except ValidationError as err:
                return err.__str__(), 400
        else:
            return "", 415
    
    @app.post("/convert")
    def convert():
        # if request.is_json:
        #     body = request.json
        #     try:
        #         convert_request = ConvertRequest.parse_obj(body)
        #         convert_unconverted = convert_request.convert_unconverted
        #         process_converted = convert_request.process_converted
        #     except ValidationError as err:
        #         return err.__str__(), 400
        exp_tracker.refresh_all()
        experiments_to_convert = exp_tracker.get_all_to_convert()
        logger.info(f"Experiments to convert: {[exp.id for exp in experiments_to_convert]}")
        for exp in experiments_to_convert:
            logger.info(f"Converting experiment {exp}")
            exp_path = Path(unconverted_data_dir, exp.id)
            data_converter.convert_neutron_data(
                config,
                config_setup,
                sources=[exp_path],
                destination=converted_data_dir,
            )
        
        exp_tracker._refresh_converted()
        experiments_to_process = exp_tracker.get_all_to_process()
        logger.info(f"Experiments to process: {[exp.id for exp in experiments_to_process]}")
        return "", 200



    @app.post("/")
    def rescan_directory():
        logger.info("Rescan triggered")
        new_directories_list = dir_watcher.find_new_directories()
        logger.info(f"New directories list: {new_directories_list}")
        new_exp_ids = [Path(dir).parts[-1] for dir in new_directories_list]
        print(f"New experiment IDs found: {new_exp_ids}")

        print("Converting Experiments...")

        for new_directory in new_directories_list:
            data_converter.convert_neutron_data(
                config,
                config_setup,
                sources=[new_directory],
                destination=converted_data_dir,
            )

        return {"new_experiments": new_exp_ids}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
