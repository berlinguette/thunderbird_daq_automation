from pydantic import BaseModel, ValidationError
from automatic_converter.experiment_inventory import Experiment, OverrideInventory
from automatic_converter.experiment_tracker import ExperimentTracker
from automatic_converter.automatic_converter import AutomaticConverter
from pathlib import Path
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

class ConvertRequest(BaseModel):
    convert_unconverted: bool = True
    process_converted: bool = True

def create_app():
    app = Flask(__name__)
    automatic_converter = AutomaticConverter(converted_data_dir)

    overrides = OverrideInventory()
    overrides.set(
        pattern="ID-(338|350)",
        has_unconverted=True,
        has_converted=True,
        has_processed=True,
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
    def add_override():
        if request.is_json:
            body = request.json
            try:
                exp = Experiment.parse_obj(body)
                overrides.set_exp(exp)
                return [exp.dict() for exp in overrides.get_all()], 201
            except ValidationError as err:
                return err.__str__(), 400
        else:
            return "", 415
    
    @app.delete("/overrides/<pattern>")
    def delete_override(pattern: str):
        overrides.experiments.pop(pattern, None)
        return [exp.dict() for exp in overrides.get_all()], 200
    
    @app.get("/convert")
    def get_status():
        status = automatic_converter.status()
        logger.info(f"Current conversion status: {status}")
        return status
    
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
            logger.info(f"Adding experiment {exp} to conversion queue")
            exp_path = Path(unconverted_data_dir, exp.id)
            automatic_converter.convert(exp_path)
        
        # exp_tracker._refresh_converted()
        # experiments_to_process = exp_tracker.get_all_to_process()
        # logger.info(f"Experiments to process: has_converted=True{[exp.id for exp in experiments_to_process]}")
        return automatic_converter.status(), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
