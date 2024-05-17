"""
Contains common fixtures/helpers that may be used across multiple tests
"""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem
import pytest
from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.experiment_inventory import OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.tests.unit.conftest import make_experiment_props


@pytest.fixture
def override_inventory():
    return OverrideInventory(Path("/foo"))


@pytest.fixture
def initialized_fs(fs: FakeFilesystem):
    """
    Initializes a fake filesystem, creating empty directories
    for unconverted, converted, and processed data directories
    """
    fs.create_dir("/unc")
    fs.create_dir("/con")
    fs.create_dir("/pro")
    yield fs


@pytest.fixture
def exp_tracker(override_inventory, initialized_fs):
    """
    Initializes a test ExperimentTracker with unconverted, converted, and processed
    data directory paths set to "/unc", "/con", and "/pro" respectively.
    A default override for experiments matching pattern /ID-1../ has also been set
    """
    override_inventory.set("ID-1..", make_experiment_props())
    return ExperimentTracker(
        Path("/unc"), Path("/con"), Path("/pro"), override_inventory
    )


@pytest.fixture
def automatic_analyzer(exp_tracker: ExperimentTracker):
    return AutomaticAnalyzer(
        {}, {}, exp_tracker, Path("/psd_python"), Path("/psd_program")
    )
