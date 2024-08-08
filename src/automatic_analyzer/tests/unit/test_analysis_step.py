from pathlib import Path
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.analysis_step import (
    UnconvertedAnalysisStep,
    ConvertedAnalysisStep,
)
from automatic_analyzer.experiment import Experiment
from automatic_analyzer.tests.conftest import make_analysis_step_props


@pytest.fixture
def experiment():
    exp_props = make_analysis_step_props([(0, False), (-1, False)])
    return Experiment(id="ID-TEST", analysis_step_props=exp_props)


class TestUnconvertedAnalysisStep:
    def test_should_convert_experiment(
        self,
        mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock],
        experiment: Experiment,
    ):
        """Test trying to convert using UnconvertedAnalysisStep.analyze()"""
        mocked_unconverted_step[0].analyze(experiment)
        assert mocked_unconverted_step[1].call_args.kwargs["sources"] == [
            Path(mocked_unconverted_step[0]._unconverted_path, experiment.id)
        ]
        assert mocked_unconverted_step[1].call_args.kwargs["destination"] == Path(
            mocked_unconverted_step[0]._converted_path
        )
        mocked_unconverted_step[1].assert_called_once()

    def test_should_find_experiments_without_error(
        self,
        initialized_fs: FakeFilesystem,
        mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock],
    ):
        """Test trying to find experiments using UnconvertedAnalysisStep.check_experiments()"""
        initialized_fs.create_dir("/unc/ID-001")
        initialized_fs.create_file("/unc/ID-001/run.info")
        initialized_fs.create_dir("/unc/ID-002")
        initialized_fs.create_file("/unc/ID-002/run.info")

        experiments = list(mocked_unconverted_step[0].check_experiments())
        assert len(experiments) == 2
        for _, props in experiments:
            assert props.mtime_present()

    def test_should_find_experiments_with_error(
        self,
        initialized_fs: FakeFilesystem,
        mocked_unconverted_step: tuple[UnconvertedAnalysisStep, MagicMock],
    ):
        """Test trying to detect errored experiments using UnconvertedAnalysisStep.check_experiments()"""
        initialized_fs.create_dir("/unc/ID-001")
        initialized_fs.create_dir("/unc/ID-002")

        experiments = list(mocked_unconverted_step[0].check_experiments())
        assert len(experiments) == 2
        for _, props in experiments:
            assert not props.mtime_present()
            assert props.mtime == "Error"


class TestConvertedAnalysisStep:
    def test_should_convert_experiment(
        self,
        converted_step: ConvertedAnalysisStep,
        experiment: Experiment,
    ):
        """Test that nothing goes wrong with ConvertedAnalysisStep.analyze() - nothing should happen"""
        converted_step.analyze(experiment)

    def test_should_find_experiments_without_error(
        self,
        initialized_fs: FakeFilesystem,
        converted_step: ConvertedAnalysisStep,
    ):
        """Test trying to find experiments using ConvertedAnalysisStep.check_experiments()"""
        initialized_fs.create_dir("/con/ID-001")
        initialized_fs.create_file(
            "/con/ID-001/conversion.log", contents="Conversion of ID-001 complete"
        )
        initialized_fs.create_dir("/con/ID-002")
        initialized_fs.create_file(
            "/con/ID-002/conversion.log", contents="Conversion of ID-002 complete"
        )

        experiments = list(converted_step.check_experiments())
        assert len(experiments) == 2
        for _, props in experiments:
            assert props.mtime_present()

    def test_should_find_experiments_with_error(
        self, initialized_fs: FakeFilesystem, converted_step: ConvertedAnalysisStep
    ):
        """Test trying to find experiments using ConvertedAnalysisStep.check_experiments()"""
        initialized_fs.create_dir("/con/ID-001")
        initialized_fs.create_file("/con/ID-001/conversion.log", contents="Error")
        initialized_fs.create_dir("/con/ID-002")

        experiments = list(converted_step.check_experiments())
        assert len(experiments) == 2
        for _, props in experiments:
            assert not props.mtime_present()
            assert props.mtime == "Error"
