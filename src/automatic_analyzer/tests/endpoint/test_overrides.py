from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem

from automatic_analyzer.experiment_inventory import Experiment
from automatic_analyzer.tests.endpoint.conftest import (
    check_experiment_valid,
    request_get_experiments,
)


class TestOverridesEndpoint:
    def get_overrides(self, client: FlaskClient):
        return request_get_experiments(client, "/overrides")

    def test_get_overrides(self, client: FlaskClient):
        """Test GET /overrides"""
        overrides = self.get_overrides(client)
        assert check_experiment_valid(overrides, "ID-1..", True, True, True, True)

    def test_should_add_override_when_post_with_valid_params(
        self, initialized_fs: FakeFilesystem, client: FlaskClient, experiment_props
    ):
        """Test POST /overrides and its effect on existing experiments"""
        initialized_fs.create_dir("/unc/ID-280")
        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, False, False, False)

        override_exp = Experiment(id="ID-2..", props=experiment_props)
        client.post("/overrides", json=override_exp.dict())

        overrides = self.get_overrides(client)
        assert check_experiment_valid(overrides, "ID-2..", True, True, True, True)

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, True, True, True)

    def test_should_return_400_when_post_with_invalid_params(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test POST /overrides with invalid override parameters"""
        response = client.post("/overrides", json={"pattern": "ID-FAKE"})
        assert response.status_code == 400

        experiments = self.get_overrides(client)
        assert next(filter(lambda exp: exp.id == "ID-FAKE", experiments), None) is None

    def test_should_delete_override_when_delete_existing_override(
        self, initialized_fs: FakeFilesystem, client: FlaskClient, experiment_props
    ):
        """Test DELETE /overrides and whether overridden experiments are reverted"""
        initialized_fs.create_dir("/unc/ID-280")
        override_exp = Experiment(id="ID-2..", props=experiment_props)
        client.post("/overrides", json=override_exp.dict())

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, True, True, True)

        client.delete("/overrides/ID-2..")

        overrides = self.get_overrides(client)
        assert not check_experiment_valid(overrides, "ID-2..", True, True, True, True)

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, False, False, False)

    def test_should_return_404_when_deleting_nonexistent_override(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test DELETE /overrides with nonexistent override pattern"""
        response = client.delete("/overrides/ID-FAKE")
        assert response.status_code == 404
