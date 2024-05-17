from typing import Literal
from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem
import pytest

from automatic_analyzer.tests.endpoint.conftest import check_experiment_valid, request_get_experiments
# from automatic_analyzer.tests.endpoint.conftest import AppTuple


class TestInventoryEndpoint:
    @pytest.fixture
    def experiments_setup_fs(self, initialized_fs: FakeFilesystem):
        initialized_fs.create_dir("/unc/ID-UNC")

        initialized_fs.create_dir("/unc/ID-UNC-CON")
        initialized_fs.create_dir("/con/ID-UNC-CON")

        initialized_fs.create_dir("/unc/ID-UNC-PRO")
        initialized_fs.create_dir("/pro/ID-UNC-PRO")

        initialized_fs.create_dir("/con/ID-CON-PRO")
        initialized_fs.create_dir("/pro/ID-CON-PRO")

        initialized_fs.create_dir("/unc/ID-ALL")
        initialized_fs.create_dir("/con/ID-ALL")
        initialized_fs.create_dir("/pro/ID-ALL")

        yield initialized_fs

    def get_experiments(
        self,
        client: FlaskClient,
        filter: None
        | Literal["all"]
        | Literal["to_be_converted"]
        | Literal["to_be_processed"]
        | Literal["to_be_analyzed"] = None,
    ):
        request_address = "/inventory"
        if filter is not None:
            request_address += f"?filter={filter}"
        
        return request_get_experiments(client, request_address)

    def test_get_all_empty(self, client: FlaskClient):
        assert len(self.get_experiments(client)) == 0
    
    def test_get_invalid_filter(self, client: FlaskClient):
        response = client.get("/inventory?filter=invalid")
        assert response.status_code == 400

    def test_get_all(self, experiments_setup_fs, client):
        experiments = self.get_experiments(client)
        assert len(experiments) == 5

        # Check default behavior is "all" filter
        assert experiments == self.get_experiments(client, "all")

        assert check_experiment_valid(experiments, "ID-UNC", True, False, False)
        assert check_experiment_valid(experiments, "ID-UNC-CON", True, True, False)
        assert check_experiment_valid(experiments, "ID-UNC-PRO", True, False, True)
        assert check_experiment_valid(experiments, "ID-CON-PRO", False, True, True)
        assert check_experiment_valid(experiments, "ID-ALL", True, True, True)

    def test_get_to_be_converted(self, experiments_setup_fs, client):
        experiments = self.get_experiments(client, "to_be_converted")
        assert len(experiments) == 2

        assert check_experiment_valid(experiments, "ID-UNC", True, False, False)
        assert check_experiment_valid(experiments, "ID-UNC-PRO", True, False, True)
    
    def test_get_to_be_processed(self, experiments_setup_fs, client):
        experiments = self.get_experiments(client, "to_be_processed")
        assert len(experiments) == 1

        assert check_experiment_valid(experiments, "ID-UNC-CON", True, True, False)
    
    def test_get_to_be_analyzed(self, experiments_setup_fs, client):
        experiments = self.get_experiments(client, "to_be_analyzed")
        assert len(experiments) == 3

        assert check_experiment_valid(experiments, "ID-UNC", True, False, False)
        assert check_experiment_valid(experiments, "ID-UNC-CON", True, True, False)
        assert check_experiment_valid(experiments, "ID-UNC-PRO", True, False, True)