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
    ):
        """
        Utility function that mocks the convert neutron data function and runs the automatic_analyzer's
        convert function, before returning the mock for assertions
        """
        with patch("data_converter.data_converter.convert_neutron_data") as mock:
            analysis = Analysis(exp=exp, params=params)
            automatic_analyzer._try_convert(analysis)
            return mock

    def test_try_convert(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert using AutomaticAnalyzer._try_convert()"""
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_called_once()

    def test_try_convert_converted_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when converted data is already present"""
        experiment.props.converted_mtime = 0
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_try_convert_unconverted_not_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when unconverted data is not present"""
        experiment.props.unconverted_mtime = -1
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_try_convert_unconverted_force(
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
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_called_once()

    def test_try_convert_unconverted_no_convert_param(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params: AnalysisParams,
        experiment: Experiment,
    ):
        """Test trying to convert when analysis_params.convert_unconverted is false"""
        analysis_params.convert_unconverted = False
        mock = self.run_mock_try_convert(
            automatic_analyzer, experiment, analysis_params
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

    def test_try_process(
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

    def test_try_process_processed_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when processed data is already present"""
        experiment.props.processed_mtime = 0
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_try_process_converted_not_present(
        self,
        automatic_analyzer: AutomaticAnalyzer,
        analysis_params,
        experiment: Experiment,
    ):
        """Test trying to convert when converted data is not present"""
        experiment.props.converted_mtime = -1
        mock = self.run_mock_try_process(
            automatic_analyzer, experiment, analysis_params
        )
        mock.assert_not_called()

    def test_try_process_converted_force(
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

    def test_try_process_converted_no_process_param(
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
