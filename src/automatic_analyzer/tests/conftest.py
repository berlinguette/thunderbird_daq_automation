"""
Contains common fixtures/helpers that may be used across multiple tests
"""

from pathlib import Path
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest
from automatic_analyzer.experiment_inventory import ExperimentProperties, OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker

def make_experiment_props():
    return ExperimentProperties(
        unconverted_mtime=0, converted_mtime=0, processed_mtime=0, overridden=False
    )

@pytest.fixture
def experiment_props():
    return make_experiment_props()

@pytest.fixture
def override_inventory():
    return OverrideInventory(Path("/foo"))

@pytest.fixture
def initialized_fs(fs: FakeFilesystem):
    fs.create_dir("/unc")
    fs.create_dir("/con")
    fs.create_dir("/pro")
    yield fs

@pytest.fixture
def exp_tracker(override_inventory, initialized_fs):
    override_inventory.set("ID-1..", make_experiment_props())
    return ExperimentTracker(Path("/unc"), Path("/con"), Path("/pro"), override_inventory)