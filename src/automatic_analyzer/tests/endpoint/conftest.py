from pathlib import Path
import threading
from typing import Literal
from unittest.mock import MagicMock
from flask import Flask
from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.analysis_step import AnalysisStep, UnconvertedAnalysisStep
from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.experiment import Experiment
from automatic_analyzer.override_inventory import Override, OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer_main import create_app

AppTuple = tuple[
    Flask, OverrideInventory, ExperimentTracker, list[AnalysisStep], AutomaticAnalyzer
]


def check_experiment_valid(
    experiments: list[Experiment],
    valid_id: str,
    step_present: list[bool],
    overridden: list[bool],
):
    def valid_experiment_pred(exp: Experiment):
        if exp.id != valid_id:
            return False
        for i, prop in enumerate(exp.analysis_step_props):
            if prop.mtime_present() != step_present[i]:
                return False
            if prop.overridden != overridden[i]:
                return False
        return True

    return next(filter(valid_experiment_pred, experiments), None) is not None


def check_override_valid(
    overrides: list[Override],
    valid_pattern: str,
    step_present: list[bool],
):
    def valid_experiment_pred(ovr: Override):
        if ovr.pattern != valid_pattern:
            return False
        for i, prop in enumerate(ovr.analysis_step_overrides):
            if prop and prop.mtime_present() != step_present[i]:
                return False
        return True

    return next(filter(valid_experiment_pred, overrides), None) is not None


def request_get_experiments(client: FlaskClient, request_address: str):
    response = client.get(request_address)
    experiments_raw = response.json
    assert experiments_raw is not None

    experiments = [Experiment.parse_obj(exp) for exp in experiments_raw]
    return experiments


def request_get_overrides(client: FlaskClient, request_address: str):
    response = client.get(request_address)
    overrides_raw = response.json
    assert overrides_raw is not None

    experiments = [Override.parse_obj(exp) for exp in overrides_raw]
    return experiments


@pytest.fixture
def test_app(
    initialized_fs,
    override_inventory: OverrideInventory,
    exp_tracker: ExperimentTracker,
    automatic_analyzer: AutomaticAnalyzer,
    mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock, threading.Event],
    converted_step,
):
    analysis_steps = [mocked_unconverted_step[0], converted_step]

    def fake_analyzer_setup():
        return (
            override_inventory,
            exp_tracker,
            automatic_analyzer,
            analysis_steps,
            Path("/logs"),
        )

    app = create_app(fake_analyzer_setup)
    app.config.update(
        {
            "TESTING": True,
        }
    )

    yield (app, override_inventory, exp_tracker, analysis_steps, automatic_analyzer)

    # clean up / reset resources here


@pytest.fixture()
def client(test_app: AppTuple, monkeypatch: pytest.MonkeyPatch):
    # disgusting workaround for importlib.metadata.version("werkzeug") being unable to find the package
    monkeypatch.setattr("importlib.metadata.version", lambda x: "3.0.2")
    yield test_app[0].test_client()


@pytest.fixture()
def runner(test_app: AppTuple):
    return test_app[0].test_cli_runner()


@pytest.fixture()
def experiments_setup_fs(initialized_fs: FakeFilesystem):
    initialized_fs.create_dir("/unc/ID-UNC")
    initialized_fs.create_file("/unc/ID-UNC/run.info")
    initialized_fs.create_dir("/unc/ID-UNC-CONERR")
    initialized_fs.create_file("/unc/ID-UNC-CONERR/run.info")

    initialized_fs.create_dir("/unc/ID-UNC-CON")
    initialized_fs.create_file("/unc/ID-UNC-CON/run.info")
    initialized_fs.create_dir("/con/ID-UNC-CON")
    initialized_fs.create_file(
        "/con/ID-UNC-CON/conversion.log", contents="Conversion of ID-UNC-CON complete"
    )
    initialized_fs.create_dir("/con/ID-UNC-CONERR")
    initialized_fs.create_file(
        "/con/ID-UNC-CONERR/conversion.log", contents="Error :(("
    )

    initialized_fs.create_dir("/con/ID-CON")
    initialized_fs.create_file(
        "/con/ID-CON/conversion.log", contents="Conversion of ID-CON complete"
    )

    yield initialized_fs
