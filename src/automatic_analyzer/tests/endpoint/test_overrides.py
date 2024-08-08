from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem

from automatic_analyzer.override_inventory import Override
from automatic_analyzer.tests.endpoint.conftest import (
    check_experiment_valid,
    check_override_valid,
    request_get_experiments,
    request_get_overrides,
)


class TestOverridesEndpoint:
    def get_overrides(self, client: FlaskClient):
        return request_get_overrides(client, "/overrides")

    def test_get_overrides(self, client: FlaskClient):
        """Test GET /overrides"""
        overrides = self.get_overrides(client)
        assert check_override_valid(overrides, "ID-1..", [True, True])

    def test_should_add_override_when_post_with_valid_params(
        self,
        initialized_fs: FakeFilesystem,
        client: FlaskClient,
        base_analysis_step_props,
    ):
        """Test POST /overrides and its effect on existing experiments"""
        initialized_fs.create_dir("/unc/ID-280")
        initialized_fs.create_file("/unc/ID-280/run.info")
        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(
            experiments, "ID-280", [True, False], [False, False]
        )

        override_exp = Override(
            pattern="ID-2..", analysis_step_overrides=base_analysis_step_props
        )
        client.post("/overrides", json=override_exp.dict())

        overrides = self.get_overrides(client)
        assert check_override_valid(overrides, "ID-2..", [True, True])

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", [True, True], [True, True])

    def test_should_return_400_when_post_with_invalid_params(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test POST /overrides with invalid override parameters"""
        response = client.post("/overrides", json={"pattern": "ID-FAKE"})
        assert response.status_code == 400

        overrides = self.get_overrides(client)
        assert (
            next(filter(lambda ovr: ovr.pattern == "ID-FAKE", overrides), None) is None
        )

    def test_should_revert_overridden_experiment_when_existing_override_deleted(
        self,
        initialized_fs: FakeFilesystem,
        client: FlaskClient,
        base_analysis_step_props,
    ):
        """Test DELETE /overrides and whether overridden experiments are reverted"""
        initialized_fs.create_dir("/unc/ID-280")
        initialized_fs.create_file("/unc/ID-280/run.info")
        override_exp = Override(
            pattern="ID-2..", analysis_step_overrides=base_analysis_step_props
        )
        client.post("/overrides", json=override_exp.dict())

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", [True, True], [True, True])

        client.delete("/overrides/ID-2..")

        overrides = self.get_overrides(client)
        assert not check_override_valid(overrides, "ID-2..", [True, True])

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(
            experiments, "ID-280", [True, False], [False, False]
        )

    def test_should_return_404_when_deleting_nonexistent_override(
        self, initialized_fs: FakeFilesystem, client: FlaskClient
    ):
        """Test DELETE /overrides with nonexistent override pattern"""
        response = client.delete("/overrides/ID-FAKE")
        assert response.status_code == 404
