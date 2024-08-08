import logging
from pathlib import Path
import re
from typing import Callable
from pydantic import ValidationError
from automatic_analyzer.analysis_config import make_analysis_steps_config
from automatic_analyzer.analysis_step import AnalysisStep
import automatic_analyzer.env_keys as env_keys
from automatic_analyzer.override_inventory import (
    Override,
    OverrideInventory,
)
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.automatic_analyzer import (
    Analysis,
    AnalysisParams,
    AnalysisRequestParams,
    AutomaticAnalyzer,
)
from automatic_analyzer.logging_handlers import follow, log_stream_filter
from loguru import logger
from flask import Flask, Response, request
from flask_cors import CORS
import sys
from datetime import datetime

from automatic_analyzer.otlp import get_otlp_log_handler


def analyzer_setup() -> (
    tuple[
        OverrideInventory,
        ExperimentTracker,
        AutomaticAnalyzer,
        list[AnalysisStep],
        Path,
    ]
):
    """
    Loads config from environment and initializes inventory tracker objects.
    The function sets up logging and loads overrides if the file exists.
    Returns override inventory, experiment tracker, automatic analyzer, and log file path
    """
    config = env_keys.load_env_config()

    today_date = datetime.today().strftime("%Y-%m-%d")
    log_file_path = Path(config.log_file_folder, f"{today_date}.log")

    logger.remove()
    logger.add(sys.stderr, level=logging.INFO)
    logger.add(
        log_file_path, level=logging.NOTSET, serialize=True, filter=log_stream_filter
    )
    logger.add(get_otlp_log_handler())
    # logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET, force=True)
    # # don't log unnecessary debug info from sh module
    # logging.getLogger("sh").setLevel(logging.INFO)

    try:
        overrides = OverrideInventory.load_from_file(config.overrides_file_path)
        logger.info(f"Loaded overrides from {config.overrides_file_path}")
    except (NotADirectoryError, FileNotFoundError, EOFError):
        overrides = OverrideInventory(config.overrides_file_path)
        logger.info("Existing overrides not found")

    analysis_steps = make_analysis_steps_config(config)
    exp_tracker = ExperimentTracker(analysis_steps, overrides)
    automatic_analyzer = AutomaticAnalyzer(exp_tracker, analysis_steps)

    return (overrides, exp_tracker, automatic_analyzer, analysis_steps, log_file_path)


def create_app(
    analyzer_setup_fn: Callable[
        [],
        tuple[
            OverrideInventory,
            ExperimentTracker,
            AutomaticAnalyzer,
            list[AnalysisStep],
            Path,
        ],
    ] = analyzer_setup,
):
    # Calls analyzer_setup() by default but can be changed for running tests
    overrides, exp_tracker, automatic_analyzer, analysis_steps, log_file_path = (
        analyzer_setup_fn()
    )

    app = Flask(__name__)
    CORS(app, origins=["*"])

    @app.get("/analysis_steps")
    def get_analysis_steps():
        return [x.name for x in analysis_steps]

    @app.get("/inventory")
    def get_inventory():
        filter = request.args.get("filter", "all")
        get_exp_mapping = {
            "all": exp_tracker.get_all_experiments,
            "to_be_analyzed": exp_tracker.get_all_to_analyze,
        }
        if filter not in get_exp_mapping:
            return "Invalid experiment filter", 400
        exp_tracker.refresh_inventory()
        return [exp.dict() for exp in get_exp_mapping[filter]()]

    @app.get("/overrides")
    def get_overrides():
        return [exp.dict() for exp in overrides.get_all()]

    @app.post("/overrides")
    def add_override():
        if request.is_json:
            body = request.json
            try:
                override = Override.parse_obj(body)
                overrides.set_exp(override)
                return [ovr.dict() for ovr in overrides.get_all()], 201
            except ValidationError as err:
                return err.__str__(), 400
        else:
            return "", 415

    @app.delete("/overrides/<pattern>")
    def delete_override(pattern: str):
        if overrides.get(pattern) is None:
            return "Experiment not found", 404
        overrides.delete(pattern)
        # for id in exp_tracker.exp_inventory.experiments.keys():
        #     # clear old experiments that used to be overridden so exp tracker won't skip it when refreshing
        #     if overrides.get_override_exp(id) is None:
        #         exp_tracker.exp_inventory.experiments[id].props.overridden = False
        return [exp.dict() for exp in overrides.get_all()], 200

    @app.get("/analyses")
    def get_analyses_status():
        status = automatic_analyzer.status()
        logger.debug(f"Current analysis queue: {status}")
        return status

    @app.post("/analyses")
    def start_analyses():
        if request.is_json:
            body = request.json
            try:
                analysis_params = AnalysisRequestParams.parse_obj(body)
                logger.info(f"Analysis params: {analysis_params}")

                exp_tracker.refresh_inventory()
                experiments_to_analyze = exp_tracker.get_all_to_analyze(
                    analysis_params.steps_to_analyze
                )
                if analysis_params.pattern is not None:
                    patt = analysis_params.pattern
                    experiments_to_analyze = [
                        exp
                        for exp in experiments_to_analyze
                        if re.search(patt, exp.id) is not None
                    ]
                logger.info(
                    f"Experiments to analyze: {[exp.id for exp in experiments_to_analyze]}"
                )
                for exp in experiments_to_analyze:
                    params = AnalysisParams(
                        steps_to_analyze=analysis_params.steps_to_analyze
                    )
                    analysis = Analysis(exp_id=exp.id, params=params)
                    automatic_analyzer.analyze(analysis)

                # Queue might be empty because analysis hasn't been put in queue yet
                status = automatic_analyzer.status()
                return status, 200
            except ValidationError as err:
                return err.__str__(), 400
        else:
            return "", 415

    @app.get("/logs")
    def listen_logs():
        def format_sse(data: str, event: str | None = None) -> str:
            msg = f"data: {data}\n\n"
            if event is not None:
                msg = f"event: {event}\n{msg}"
            return msg

        def log_reader():
            with open(log_file_path, "r") as file:
                for line in follow(file):
                    yield format_sse(line)

        return Response(log_reader(), mimetype="text/event-stream")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
