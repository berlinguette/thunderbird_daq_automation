from typing import Literal
from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.tests.endpoint.conftest import (
    check_experiment_valid,
    request_get_experiments,
)
# from automatic_analyzer.tests.endpoint.conftest import AppTuple


class TestInventoryEndpoint:
    def get_experiments(
        self,
        client: FlaskClient,
        filter: None | Literal["all"] | Literal["to_be_analyzed"] = None,
    ):
        request_address = "/inventory"
        if filter is not None:
            request_address += f"?filter={filter}"

        return request_get_experiments(client, request_address)

    def test_should_initially_be_empty(self, client: FlaskClient):
        assert len(self.get_experiments(client)) == 0

    def test_should_return_400_when_filter_invalid(self, client: FlaskClient):
        response = client.get("/inventory?filter=invalid")
        assert response.status_code == 400

    def test_should_return_all_experiments_when_filter_all_or_null(
        self, experiments_setup_fs, client
    ):
        """Test GET /inventory and GET /inventory?filter=all"""
        experiments = self.get_experiments(client)
        assert len(experiments) == 4

        # Check default behavior is "all" filter
        assert experiments == self.get_experiments(client, "all")

        assert check_experiment_valid(
            experiments, "ID-UNC", [True, False], [False, False]
        )
        assert check_experiment_valid(
            experiments, "ID-UNC-CON", [True, True], [False, False]
        )
        assert check_experiment_valid(
            experiments, "ID-UNC-CONERR", [True, False], [False, False]
        )
        assert check_experiment_valid(
            experiments, "ID-CON", [False, True], [False, False]
        )

    def test_should_return_analyzable_experiments_when_filter_to_be_analyzed(
        self, experiments_setup_fs, client
    ):
        """Test GET /inventory?filter=to_be_analyzed"""
        experiments = self.get_experiments(client, "to_be_analyzed")
        assert len(experiments) == 2

        assert check_experiment_valid(
            experiments, "ID-UNC", [True, False], [False, False]
        )
        assert check_experiment_valid(
            experiments, "ID-UNC-CONERR", [True, False], [False, False]
        )
