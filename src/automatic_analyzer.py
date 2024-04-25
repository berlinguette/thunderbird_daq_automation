from pydantic import ValidationError
from automatic_analyzer.experiment_inventory import (
    Experiment,
    ExperimentProperties,
    OverrideInventory,
)
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.automatic_analyzer import (
    Analysis,
    AnalysisParams,
    AutomaticAnalyzer,
)
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


def create_app():
    app = Flask(__name__)
    automatic_analyzer = AutomaticAnalyzer(
        unconverted_data_dir, converted_data_dir, processed_data_dir
    )

    overrides = OverrideInventory()
    overrides.set(
        pattern="ID-(338|350)",
        props=ExperimentProperties(
            unconverted_mtime=0, converted_mtime=0, processed_mtime=0, overridden=True
        ),
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

    @app.get("/analyze")
    def get_analyze_status():
        status = automatic_analyzer.status()
        logger.info(f"Current analysis status: {status}")
        return status

    @app.post("/analyze")
    def start_analyze():
        analysis_params = AnalysisParams()
        if request.is_json:
            body = request.json
            try:
                analysis_params = AnalysisParams.parse_obj(body)
            except ValidationError as err:
                return err.__str__(), 400
        exp_tracker.refresh_all()
        experiments_to_convert = exp_tracker.get_all_to_convert()
        logger.info(
            f"Experiments to analyze: {[exp.id for exp in experiments_to_convert]}"
        )
        for exp in experiments_to_convert:
            analysis = Analysis(exp=exp, params=analysis_params)
            automatic_analyzer.analyze(analysis)

        # exp_tracker._refresh_converted()
        # experiments_to_process = exp_tracker.get_all_to_process()
        # logger.info(f"Experiments to process: has_converted=True{[exp.id for exp in experiments_to_process]}")

        # Queue might be empty because analysis hasn't been put in queue yet
        status = automatic_analyzer.status()
        logger.info(f"Current analysis status: {status}")
        return status, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
