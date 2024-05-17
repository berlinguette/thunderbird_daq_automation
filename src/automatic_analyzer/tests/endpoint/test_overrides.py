from flask.testing import FlaskClient
from pyfakefs.fake_filesystem import FakeFilesystem

from automatic_analyzer.experiment_inventory import Experiment
from automatic_analyzer.tests.endpoint.conftest import check_experiment_valid, request_get_experiments


class TestOverridesEndpoint:
    def get_overrides(self, client: FlaskClient):
        return request_get_experiments(client, "/overrides")

    def test_get_overrides(self, client: FlaskClient):
        overrides = self.get_overrides(client)
        assert check_experiment_valid(overrides, "ID-1..", True, True, True, True)
    

    def test_add_override(self, initialized_fs: FakeFilesystem, client: FlaskClient, experiment_props):
        initialized_fs.create_dir("/unc/ID-280")
        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, False, False, False)

        override_exp = Experiment(id="ID-2..", props=experiment_props)
        client.post("/overrides", json=override_exp.dict()) 

        overrides = self.get_overrides(client)
        assert check_experiment_valid(overrides, "ID-2..", True, True, True, True)

        experiments = request_get_experiments(client, "/inventory")
        assert check_experiment_valid(experiments, "ID-280", True, True, True, True)
    
    def test_delete_override(self, initialized_fs: FakeFilesystem, client: FlaskClient, experiment_props):
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