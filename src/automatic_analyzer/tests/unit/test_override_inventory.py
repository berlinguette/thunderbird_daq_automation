from pathlib import Path
import pickle
import pytest
from unittest.mock import patch, mock_open
from automatic_analyzer.analysis_step import BaseAnalysisStepProps
from automatic_analyzer.override_inventory import (
    Override,
    OverrideInventory,
)
from automatic_analyzer.tests.conftest import (
    make_base_analysis_step_props,
)


class TestOverrideInventory:
    @pytest.fixture
    def override(self):
        return Override(
            pattern="ID-TEST", analysis_step_overrides=make_base_analysis_step_props()
        )

    def test_should_load_inventory_from_pickle_file(self, override: Override):
        """Test loading existing override inventory from pickle file with OverrideInventory.load_from_file()"""
        override_inventory = OverrideInventory(Path("/foo"), {"ID-TEST": override})
        overrides_pickle = pickle.dumps(override_inventory)

        with patch("builtins.open", mock_open(read_data=overrides_pickle)):
            loaded_overrides = OverrideInventory.load_from_file(Path("/foo"))
            assert loaded_overrides.get("ID-TEST") == override

    @patch("builtins.open", mock_open())
    def test_should_set_new_override(
        self,
        override_inventory: OverrideInventory,
        base_analysis_step_props: list[BaseAnalysisStepProps | None],
    ):
        """Test adding an override with OverrideInventory.set()"""

        # Automatically set Experiment.props.overridden to true
        override_inventory.set("ID-TEST", base_analysis_step_props)
        exp_test = override_inventory.get("ID-TEST")
        assert exp_test is not None
        assert exp_test.analysis_step_overrides == base_analysis_step_props
    
    @patch("builtins.open", mock_open())
    def test_should_delete_override(self, override_inventory: OverrideInventory, override: Override):
        """Test deleting existing and nonexisting overrides with OverrideInventory.delete()"""

        override_inventory.set_exp(override)
        assert override_inventory.get("ID-TEST") == override

        override_inventory.delete("ID-TEST")
        assert override_inventory.get("ID-TEST") is None

        assert override_inventory.get("ID-FAKE") is None
        override_inventory.delete("ID-FAKE")
        assert override_inventory.get("ID-FAKE") is None


    @patch("builtins.open", mock_open())
    def test_should_get_override_that_matches_pattern(
        self,
        override_inventory: OverrideInventory,
        base_analysis_step_props: list[BaseAnalysisStepProps | None],
    ):
        """Test matching an override pattern to a given experiment ID using OverrideInventory.get_override_exp()"""
        override_inventory.set("ID-100", base_analysis_step_props)
        override_inventory.set("ID-2..", base_analysis_step_props)

        # Direct match
        id_100 = override_inventory.get_override_exp("ID-100")
        assert id_100 is not None
        if id_100 is not None:
            assert id_100.pattern == "ID-100"

        # Pattern match
        id_2_dot_dot = override_inventory.get_override_exp("ID-245")
        assert id_2_dot_dot is not None
        if id_2_dot_dot is not None:
            assert id_2_dot_dot.pattern == "ID-2.."

        assert override_inventory.get_override_exp("ID-023") is None
