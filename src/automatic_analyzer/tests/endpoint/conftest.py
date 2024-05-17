from pathlib import Path
from flask import Flask
from flask.testing import FlaskClient
import pytest

from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.experiment_inventory import Experiment, OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer_main import create_app

AppTuple = tuple[Flask, OverrideInventory, ExperimentTracker, AutomaticAnalyzer]


def check_experiment_valid(
    experiments: list[Experiment],
    valid_id: str,
    unconverted_present: bool,
    converted_present: bool,
    processed_present: bool,
    overridden: bool = False
):
    def valid_experiment_pred(exp: Experiment):
        if exp.id != valid_id:
            return False
        if unconverted_present and exp.props.unconverted_mtime == -1:
            return False
        if converted_present and exp.props.converted_mtime == -1:
            return False
        if processed_present and exp.props.processed_mtime == -1:
            return False
        if overridden and not exp.props.overridden:
            return False
        return True

    assert next(filter(valid_experiment_pred, experiments), None) is not None

def request_get_experiments(client: FlaskClient, request_address: str):
    response = client.get(request_address)
    experiments_raw = response.json
    assert experiments_raw is not None

    experiments = [Experiment.parse_obj(exp) for exp in experiments_raw]
    return experiments

@pytest.fixture()
def test_app(
    initialized_fs,
    override_inventory: OverrideInventory,
    exp_tracker: ExperimentTracker,
    automatic_analyzer: AutomaticAnalyzer,
):
    def fake_analyzer_setup():
        return (override_inventory, exp_tracker, automatic_analyzer, Path("/logs"))

    app = create_app(fake_analyzer_setup)
    app.config.update(
        {
            "TESTING": True,
        }
    )

    yield (app, override_inventory, exp_tracker, automatic_analyzer)

    # clean up / reset resources here


@pytest.fixture()
def client(test_app: AppTuple, monkeypatch: pytest.MonkeyPatch):
    # disgusting workaround for importlib.metadata.version("werkzeug") being unable to find the package
    monkeypatch.setattr("importlib.metadata.version", lambda x: "3.0.2")
    yield test_app[0].test_client()


@pytest.fixture()
def runner(test_app: AppTuple):
    return test_app[0].test_cli_runner()
