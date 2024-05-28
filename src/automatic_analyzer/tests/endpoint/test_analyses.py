from pathlib import Path
from time import sleep
from unittest.mock import MagicMock, patch
from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.automatic_analyzer import AutomaticAnalyzer
from automatic_analyzer.tests.endpoint.conftest import AppTuple

MockAppTuple = tuple[AutomaticAnalyzer, MagicMock, MagicMock]


def assert_mock_convert_args(unconverted_paths: list[str], mock_convert: MagicMock):
    mock_convert.assert_called()
    assert len(mock_convert.call_args_list) == len(unconverted_paths)
    for i, path in enumerate(unconverted_paths):
        assert mock_convert.call_args_list[i].kwargs["sources"] == [Path(path)]
        assert mock_convert.call_args_list[i].kwargs["destination"] == Path("/con")


def assert_mock_process_args(converted_ids_input: list[str], mock_process: MagicMock):
    mock_process.assert_called()
    assert len(mock_process.call_args_list) == len(converted_ids_input)
    for i, path in enumerate(converted_ids_input):
        assert path in mock_process.call_args_list[i].kwargs["input"]


class TestAnalysesEndpoint:
    @pytest.fixture
    def mocked_test_app(self, test_app: AppTuple):
        app, override_inventory, exp_tracker, automatic_analyzer = test_app
        with patch(
            "data_converter.data_converter.convert_neutron_data"
        ) as mock_convert:
            with patch("subprocess.run") as mock_process:
                yield (automatic_analyzer, mock_convert, mock_process)

    def test_should_return_400_when_post_with_invalid_params(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test POST /analyses with invalid params"""
        response = client.post(
            "/analyses", json={"convert_unconverted": "Don't coerce"}
        )
        assert response.status_code == 400

    def test_should_try_analyze_all_experiments(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments"""
        automatic_analyzer, mock_convert, mock_process = mocked_test_app

        client.post("/analyses")
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_called()
        assert len(mock_convert.call_args_list) == 2
        assert mock_convert.call_args_list[0].kwargs["sources"] == [Path("/unc/ID-UNC")]
        assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")
        assert mock_convert.call_args_list[1].kwargs["sources"] == [
            Path("/unc/ID-UNC-PRO")
        ]
        assert mock_convert.call_args_list[1].kwargs["destination"] == Path("/con")

        mock_process.assert_called_once()

    def test_analyze_convert_only(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments that can be converted"""
        automatic_analyzer, mock_convert, mock_process = mocked_test_app

        # convert_unconverted is already default True
        client.post("/analyses", json={"process_converted": False})
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_called()
        assert len(mock_convert.call_args_list) == 2
        assert mock_convert.call_args_list[0].kwargs["sources"] == [Path("/unc/ID-UNC")]
        assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")
        assert mock_convert.call_args_list[1].kwargs["sources"] == [
            Path("/unc/ID-UNC-PRO")
        ]
        assert mock_convert.call_args_list[1].kwargs["destination"] == Path("/con")

        mock_process.assert_not_called()

    def test_analyze_process_only(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments that can be processed"""
        automatic_analyzer, mock_convert, mock_process = mocked_test_app

        # process_converted is already default True
        client.post("/analyses", json={"convert_unconverted": False})
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_not_called()

        mock_process.assert_called_once()

    def test_analyze_match_pattern(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses on all experiments that match a pattern"""
        automatic_analyzer, mock_convert, mock_process = mocked_test_app

        # convert_unconverted is already default True
        client.post("/analyses", json={"pattern": "ID-UNC-.*"})
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)
        mock_convert.assert_called_once()
        assert mock_convert.call_args_list[0].kwargs["sources"] == [
            Path("/unc/ID-UNC-PRO")
        ]
        assert mock_convert.call_args_list[0].kwargs["destination"] == Path("/con")

        mock_process.assert_called_once()

    def test_analyze_force(
        self,
        experiments_setup_fs: FakeFilesystem,
        mocked_test_app: MockAppTuple,
        client: FlaskClient,
    ):
        """Test POST /analyses with force enabled"""
        automatic_analyzer, mock_convert, mock_process = mocked_test_app

        # convert_unconverted is already default True
        client.post("/analyses", json={"force": True})
        while not automatic_analyzer._analysis_queue.empty():
            sleep(0.1)

        assert_mock_convert_args(
            ["/unc/ID-UNC", "/unc/ID-UNC-CON", "/unc/ID-UNC-PRO"], mock_convert
        )

        assert_mock_process_args(["UNC", "UNC-CON", "UNC-PRO"], mock_process)
