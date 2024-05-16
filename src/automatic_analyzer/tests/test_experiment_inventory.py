from pathlib import Path
import pickle
import pytest
from unittest.mock import patch, mock_open
from automatic_analyzer.experiment_inventory import (
    Experiment,
    ExperimentDict,
    ExperimentInventory,
    ExperimentProperties,
    OverrideInventory,
)
from automatic_analyzer.tests.conftest import make_experiment_props


def check_exp_props(exp: Experiment | None, props_to_check: ExperimentProperties):
    assert exp is not None
    if exp is not None:
        assert exp.props == props_to_check


class TestExperimentDict:
    """Testing ExperimentDict.set_exp() is not necessary since all it does is call set()"""

    @pytest.fixture
    def experiment_dict(self):
        return ExperimentDict()

    def test_set_new_exp(self, experiment_dict: ExperimentDict, experiment_props):
        """Test adding a new experiment with ExperimentDict.set()"""
        assert experiment_dict.get("ID-TEST") is None
        experiment_dict.set("ID-TEST", experiment_props)
        exp_test = experiment_dict.get("ID-TEST")
        check_exp_props(exp_test, experiment_props)

    def test_set_overwrite_exp(self, experiment_dict: ExperimentDict, experiment_props):
        """Test overwriting an existing experiment with ExperimentDict.set()"""
        experiment_dict.set("ID-TEST", experiment_props)

        new_experiment_props = ExperimentProperties(
            unconverted_mtime=100,
            converted_mtime=200,
            processed_mtime=300,
            overridden=True,
        )
        experiment_dict.set("ID-TEST", new_experiment_props)
        check_exp_props(experiment_dict.get("ID-TEST"), new_experiment_props)

    def test_set_overwrite_some(
        self, experiment_dict: ExperimentDict, experiment_props
    ):
        """Test overwriting only some props of an existing experiment with ExperimentDict.set()"""
        experiment_dict.set("ID-TEST", experiment_props)

        new_experiment_props = ExperimentProperties(
            unconverted_mtime=100,
            converted_mtime=None,
            processed_mtime=300,
            overridden=True,
        )
        experiment_dict.set("ID-TEST", new_experiment_props)

        check_experiment_props = ExperimentProperties(
            unconverted_mtime=100,
            converted_mtime=0,
            processed_mtime=300,
            overridden=True,
        )
        check_exp_props(experiment_dict.get("ID-TEST"), check_experiment_props)


class TestOverrideInventory:
    @pytest.fixture
    def experiment(self):
        return Experiment(id="ID-TEST", props=make_experiment_props())

    def test_load_from_file(self, override_inventory: OverrideInventory, experiment):
        """Test loading existing override inventory from pickle file with OverrideInventory.load_from_file()"""
        override_inventory.experiments["ID-TEST"] = experiment
        overrides_pickle = pickle.dumps(override_inventory)

        with patch("builtins.open", mock_open(read_data=overrides_pickle)):
            loaded_overrides = OverrideInventory.load_from_file(Path("/foo"))
            assert loaded_overrides.get("ID-TEST") == experiment

    @patch("builtins.open", mock_open())
    def test_set(
        self,
        override_inventory: OverrideInventory,
        experiment_props: ExperimentProperties,
    ):
        """Test adding an override with OverrideInventory.set()"""

        # Automatically set Experiment.props.overridden to true
        assert not experiment_props.overridden
        override_inventory.set("ID-TEST", experiment_props)
        exp_test = override_inventory.get("ID-TEST")
        assert exp_test is not None
        if exp_test is not None:
            assert exp_test.props.overridden

    @patch("builtins.open", mock_open())
    def test_get_override_exp(
        self,
        override_inventory: OverrideInventory,
        experiment_props: ExperimentProperties,
    ):
        """Test matching an override pattern to a given experiment ID using OverrideInventory.get_override_exp()"""
        override_inventory.set("ID-100", experiment_props)
        override_inventory.set("ID-2..", experiment_props)

        # Direct match
        id_100 = override_inventory.get_override_exp("ID-100")
        assert id_100 is not None
        if id_100 is not None:
            assert id_100.id == "ID-100"

        # Pattern match
        id_2_dot_dot = override_inventory.get_override_exp("ID-245")
        assert id_2_dot_dot is not None
        if id_2_dot_dot is not None:
            assert id_2_dot_dot.id == "ID-2.."

        assert override_inventory.get_override_exp("ID-023") is None


class TestExperimentInventory:
    @pytest.fixture
    def new_exp_props(self):
        return ExperimentProperties(
            unconverted_mtime=100,
            converted_mtime=100,
            processed_mtime=100,
            overridden=False,
        )

    @pytest.fixture
    def exp_inventory(self, override_inventory, experiment_props):
        with patch("builtins.open", mock_open()):
            override_inventory.set("ID-3..", experiment_props)
            return ExperimentInventory(override_inventory)

    def test_set_non_overridden(
        self, exp_inventory: ExperimentInventory, new_exp_props
    ):
        exp_inventory.set("ID-200", new_exp_props)
        check_exp_props(exp_inventory.get("ID-200"), new_exp_props)

    def test_set_overridden(self, exp_inventory: ExperimentInventory, new_exp_props):
        exp_inventory.set("ID-342", new_exp_props)

        id_3_dot_dot = exp_inventory._override_inventory.get("ID-3..")
        assert id_3_dot_dot is not None
        if id_3_dot_dot is not None:
            check_exp_props(exp_inventory.get("ID-342"), id_3_dot_dot.props)
