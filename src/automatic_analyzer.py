import logging
from pathlib import Path
import re
from pydantic import ValidationError
import automatic_analyzer.env_keys as env_keys
from automatic_analyzer.experiment_inventory import (
    Experiment,
    OverrideInventory,
)
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.automatic_analyzer import (
    Analysis,
    AnalysisParams,
    AutomaticAnalyzer,
)
from loguru import logger
from flask import Flask, request
from flask_cors import CORS
import sys
from datetime import datetime

def analyzer_setup() -> tuple[OverrideInventory, ExperimentTracker, AutomaticAnalyzer]:
    config = env_keys.load_env_config()

    today_date = datetime.today().strftime("%Y-%m-%d")
    log_file_path = Path(config.log_file_folder, f"{today_date}.log")

    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_file_path, level=logging.NOTSET)

    try:
        overrides = OverrideInventory.load_from_file(config.overrides_file_path)
        logger.info(f"Loading overrides from {config.overrides_file_path}")
    except (NotADirectoryError, FileNotFoundError, EOFError):
        overrides = OverrideInventory(config.overrides_file_path)
        logger.info("Existing overrides not found")

    exp_tracker = ExperimentTracker(
        config.unconverted_data_dir, config.converted_data_dir, config.processed_data_dir, overrides
    )

    automatic_analyzer = AutomaticAnalyzer(
        exp_tracker,
        config.unconverted_data_dir,
        config.converted_data_dir,
        config.processed_data_dir,
        config.psd_python_binary_path,
        config.psd_program_path,
    )

    return (overrides, exp_tracker, automatic_analyzer)

def create_app():
    overrides, exp_tracker, automatic_analyzer = analyzer_setup()

    app = Flask(__name__)
    CORS(app, origins=["*"])

    @app.get("/inventory")
    def get_inventory():
        exp_filter = request.args.get("filter", "all")
        get_exp_mapping = {
            "all": exp_tracker.get_all_experiments,
            "to_be_converted": exp_tracker.get_all_to_convert,
            "to_be_processed": exp_tracker.get_all_to_process,
            "to_be_analyzed": exp_tracker.get_all_to_analyze,
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
        for id in exp_tracker.experiments.experiments.keys():
            if overrides.get_override_exp(id) is not None:
                exp_tracker.experiments.experiments[id].props.overridden = False
        overrides._save_to_file()
        return [exp.dict() for exp in overrides.get_all()], 200

    @app.get("/analyses")
    def get_analyses_status():
        status = automatic_analyzer.status()
        logger.info(f"Current analysis queue: {status}")
        return status

    @app.post("/analyses")
    def start_analyses():
        analysis_params = AnalysisParams()
        if request.is_json:
            body = request.json
            try:
                analysis_params = AnalysisParams.parse_obj(body)
                logger.info(f"Analysis params: {analysis_params}")
            except ValidationError as err:
                return err.__str__(), 400
        exp_tracker.refresh_all()
        experiments_to_analyze = exp_tracker.get_all_to_analyze()
        if analysis_params.pattern is not None:
            patt = analysis_params.pattern
            logger.info(f"Filtering experiments by pattern '{patt}'")
            experiments_to_analyze = [
                exp
                for exp in experiments_to_analyze
                if re.search(patt, exp.id) is not None
            ]
        logger.info(
            f"Experiments to analyze: {[exp.id for exp in experiments_to_analyze]}"
        )
        for exp in experiments_to_analyze:
            analysis = Analysis(exp=exp, params=analysis_params)
            automatic_analyzer.analyze(analysis)

        # Queue might be empty because analysis hasn't been put in queue yet
        status = automatic_analyzer.status()
        logger.info(f"Current analysis status: {status}")
        return status, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
