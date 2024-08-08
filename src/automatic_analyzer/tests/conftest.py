"""
Contains common fixtures/helpers that may be used across multiple tests
"""

from pathlib import Path
import threading
from typing import Literal
from unittest.mock import MagicMock, patch

from pyfakefs.fake_filesystem import FakeFilesystem
import pytest
from automatic_analyzer.analysis_step import (
    AnalysisStepProps,
    BaseAnalysisStepProps,
    ConvertedAnalysisStep,
    UnconvertedAnalysisStep,
)
from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.override_inventory import OverrideInventory


def make_analysis_step_props(
    props: list[tuple[float | Literal["Error"], bool]] = [(0, False), (0, False)],
):
    return [AnalysisStepProps(mtime=mtime, overridden=ovr) for mtime, ovr in props]


def make_base_analysis_step_props(
    props: list[float | Literal["Error"] | None] = [0, 0],
):
    return [
        BaseAnalysisStepProps(mtime=mtime) if mtime is not None else None
        for mtime in props
    ]


@pytest.fixture
def analysis_step_props():
    return make_analysis_step_props()


@pytest.fixture
def base_analysis_step_props():
    return make_base_analysis_step_props()


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
    yield fs


@pytest.fixture
def mocked_unconverted_step():
    mock_event = threading.Event()

    def mock_function_with_event(*args, **kwargs):
        mock_event.set()

    with patch("data_converter.data_converter.convert_neutron_data") as mock:
        mock.side_effect = mock_function_with_event
        yield (
            UnconvertedAnalysisStep(
                "Unconverted Data", Path("/unc"), Path("/con"), {}, {}
            ),
            mock,
            mock_event,
        )


@pytest.fixture
def converted_step():
    return ConvertedAnalysisStep("Converted Data", Path("/con"))


@pytest.fixture
def exp_tracker(
    override_inventory: OverrideInventory,
    initialized_fs,
    mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock, threading.Event],
    converted_step,
):
    """
    Initializes a test ExperimentTracker with unconverted, converted, and processed
    data directory paths set to "/unc", "/con", and "/pro" respectively.
    A default override for experiments matching pattern `ID-1..` has also been set
    """
    override_inventory.set("ID-1..", make_base_analysis_step_props())
    yield ExperimentTracker(
        [mocked_unconverted_step[0], converted_step], override_inventory
    )


@pytest.fixture
def automatic_analyzer(
    exp_tracker: ExperimentTracker,
    mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock, threading.Event],
    converted_step,
):
    yield AutomaticAnalyzer(exp_tracker, [mocked_unconverted_step[0], converted_step])
