from pathlib import Path
import threading
from time import sleep
from unittest.mock import MagicMock, patch
from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.analysis_step import UnconvertedAnalysisStep
from automatic_analyzer.automatic_analyzer import (
    AnalysisRequestParams,
    AutomaticAnalyzer,
)
from automatic_analyzer.tests.endpoint.conftest import AppTuple

MockAppTuple = tuple[AutomaticAnalyzer, MagicMock, threading.Event]


def assert_mock_convert_args(
    unconverted_paths: list[str], mock_convert: MagicMock, mock_event: threading.Event
):
    assert mock_event.wait(
        timeout=1.0
    ), "Mocked function was not called within the timeout period"
    mock_convert.assert_called()
    assert len(mock_convert.call_args_list) == len(unconverted_paths)
    for i, path in enumerate(unconverted_paths):
        assert mock_convert.call_args_list[i].kwargs["sources"] == [Path(path)]
        assert mock_convert.call_args_list[i].kwargs["destination"] == Path("/con")


class TestAnalysesEndpoint:
    @pytest.fixture
    def mocked_test_app(
        self,
        test_app: AppTuple,
        mocked_unconverted_step: tuple[
            UnconvertedAnalysisStep, MagicMock, threading.Event
        ],
    ):
        app, override_inventory, exp_tracker, analysis_steps, automatic_analyzer = (
            test_app
        )
        yield (
            automatic_analyzer,
            mocked_unconverted_step[1],
            mocked_unconverted_step[2],
        )

    def test_should_return_400_when_post_with_invalid_params(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test POST /analyses with invalid params"""
        response = client.post("/analyses", json={"pattern": "Don't coerce"})
        assert response.status_code == 400

    def test_should_try_analyze_all_experiments(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments"""
        automatic_analyzer, mock_convert, mock_event = mocked_test_app

        request_params = AnalysisRequestParams(steps_to_analyze=[True])
        client.post("/analyses", json=request_params.dict())
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_called()
        assert len(mock_convert.call_args_list) == 2
        assert mock_convert.call_args_list[0].kwargs["sources"] == [Path("/unc/ID-UNC")]
        assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")
        assert mock_convert.call_args_list[1].kwargs["sources"] == [
            Path("/unc/ID-UNC-CONERR")
        ]
        assert mock_convert.call_args_list[1].kwargs["destination"] == Path("/con")

    # def test_analyze_convert_only(
    #     self,
    #     experiments_setup_fs: FakeFilesystem,
    #     mocked_test_app: MockAppTuple,
    #     client: FlaskClient,
    # ):
    #     """Test POST /analyses on all experiments that can be converted"""
    #     automatic_analyzer, mock_convert, mock_event = mocked_test_app

    #     # convert_unconverted is already default True
    #     client.post("/analyses", json={"process_converted": False})
    #     while not automatic_analyzer._analysis_queue.empty():
    #         sleep(0.1)
    #     mock_convert.assert_called()
    #     assert len(mock_convert.call_args_list) == 2
    #     assert mock_convert.call_args_list[0].kwargs["sources"] == [Path("/unc/ID-UNC")]
    #     assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")
    #     assert mock_convert.call_args_list[1].kwargs["sources"] == [
    #         Path("/unc/ID-UNC-PRO")
    #     ]
    #     assert mock_convert.call_args_list[1].kwargs["destination"] == Path("/con")

    def test_analyze_match_pattern(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments that match a pattern"""
        automatic_analyzer, mock_convert, mock_event = mocked_test_app

        # convert_unconverted is already default True
        request_params = AnalysisRequestParams(
            steps_to_analyze=[True], pattern="ID-UNC-.*"
        )
        client.post("/analyses", json=request_params.dict())
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_called_once()
        assert mock_convert.call_args_list[0].kwargs["sources"] == [
            Path("/unc/ID-UNC-CONERR")
        ]
        assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")
