from pathlib import Path
from unittest.mock import patch
import pytest

from automatic_analyzer.automatic_analyzer import (
    Analysis,
    AnalysisParams,
    AutomaticAnalyzer,
)
from automatic_analyzer.experiment_inventory import Experiment
from automatic_analyzer.tests.conftest import make_experiment_props


@pytest.fixture
def analysis_params():
    return AnalysisParams(convert_unconverted=True, process_converted=True)


class TestAutomaticAnalyzerConvert:
    @pytest.fixture
    def experiment(self):
        exp_props = make_experiment_props(0, -1, -1)
        return Experiment(id="ID-TEST", props=exp_props)

    def run_mock_try_convert(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        exp: Experiment,
        params: AnalysisParams,
        source_path: Path | None,
        dest_path: Path | None,
    ):
        """
        Utility function that mocks the convert neutron data function and runs the automatic_analyzer's
        convert function, before returning the mock for assertions
        """
        with patch("data_converter.data_converter.convert_neutron_data") as mock:
            analysis = Analysis(exp=exp, params=params)
            automatic_analyzer._try_convert(analysis)
            if source_path is not None and dest_path is not None:
                assert mock.call_args.kwargs["sources"] == [source_path]
                assert mock.call_args.kwargs["destination"] == dest_path
            return mock

    def test_should_convert_convertable_experiment(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert using AutomaticAnalyzer._try_convert()"""
        mock = self.run_mock_try_convert(
            automatic_analyzer,
            experiment,
            analysis_params,
            Path(automatic_analyzer.exp_tracker._unconverted_data_dir, experiment.id),
            Path(automatic_analyzer.exp_tracker._converted_data_dir),
        )
        mock.assert_called_once()

    def test_should_not_convert_when_converted_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when converted data is already present"""
        experiment.props.converted_mtime = 0
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params, None, None
        )
        mock.assert_not_called()

    def test_should_not_convert_when_unconverted_not_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when unconverted data is not present"""
        experiment.props.unconverted_mtime = -1
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params, None, None
        )
        mock.assert_not_called()

    def test_should_always_convert_when_force_true(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params: AnalysisParams,
        experiment: Experiment,
    ):
        """Test trying to convert when analysis_params.force is true"""
        experiment.props.unconverted_mtime = -1
        experiment.props.converted_mtime = 0
        analysis_params.force = True
        mock = self.run_mock_try_convert(
            automatic_analyzer,
            experiment,
            analysis_params,
            Path(automatic_analyzer.exp_tracker._unconverted_data_dir, experiment.id),
            Path(automatic_analyzer.exp_tracker._converted_data_dir),
        )
        mock.assert_called_once()

    def test_should_not_convert_when_convert_analysis_param_not_set(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params: AnalysisParams,
        experiment: Experiment,
    ):
        """Test trying to convert when analysis_params.convert_unconverted is false"""
        analysis_params.convert_unconverted = False
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params, None, None
        )
        mock.assert_not_called()


class TestAutomaticAnalyzerProcess:
    @pytest.fixture
    def experiment(self):
        exp_props = make_experiment_props(0, 0, -1)
        return Experiment(id="ID-TEST", props=exp_props)

    def run_mock_try_process(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        exp: Experiment,
        params: AnalysisParams,
    ):
        """
        Utility function that mocks the subprocess.run() call to the PSD analysis script
        and runs the automatic_analyzer's process function, before returning the mock for assertions
        """
        with patch("subprocess.run") as mock:
            analysis = Analysis(exp=exp, params=params)
            automatic_analyzer._try_process(analysis)
            return mock

    def test_should_process_processable_experiment(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to process using AutomaticAnalyzer._try_process()"""
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_called_once()

    def test_should_not_process_when_processed_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to process when processed data is already present"""
        experiment.props.processed_mtime = 0
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_should_not_process_when_converted_not_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to process when converted data is not present"""
        experiment.props.converted_mtime = -1
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_should_always_process_when_force_true(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params: AnalysisParams,
        experiment: Experiment,
    ):
        """Test trying to process when analysis_params.force is true"""
        experiment.props.processed_mtime = 0
        experiment.props.converted_mtime = -1
        analysis_params.force = True
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_called_once()

    def test_should_not_process_when_process_analysis_param_not_set(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params: AnalysisParams,
        experiment: Experiment,
    ):
        """Test trying to process when analysis_params.process_unprocessed is false"""
        analysis_params.process_converted = False
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()
