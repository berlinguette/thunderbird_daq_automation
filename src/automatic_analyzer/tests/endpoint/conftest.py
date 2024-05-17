from pathlib import Path
from flask import Flask
import pytest

from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.experiment_inventory import OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer_main import create_app

AppTuple = tuple[Flask, OverrideInventory, ExperimentTracker, AutomaticAnalyzer]


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
