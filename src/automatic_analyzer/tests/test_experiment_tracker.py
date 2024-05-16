from pathlib import Path
import pytest

from automatic_analyzer.experiment_inventory import OverrideInventory
from automatic_analyzer.experiment_tracker import ExperimentTracker
from automatic_analyzer.tests.helpers import make_experiment_props
from pyfakefs.fake_filesystem import FakeFilesystem

class TestExperimentTracker:
    @pytest.fixture
    def initialized_fs(self, fs: FakeFilesystem):
        fs.create_dir("/unc")
        fs.create_dir("/con")
        fs.create_dir("/pro")
        yield fs

    @pytest.fixture
    def exp_tracker(self):
        overrides = OverrideInventory(Path("/foo"))
        overrides.set("ID-1..", make_experiment_props())
        return ExperimentTracker(Path("/unc"), Path("/con"), Path("/pro"), overrides)

    def test_refresh_unconverted(self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker):
        initialized_fs.create_dir("/unc/ID-001")
        initialized_fs.create_dir("/unc/ID-100") # overridden
        
        assert len(exp_tracker.get_all_to_convert()) == 0
        exp_tracker._refresh_unconverted()
        assert len(exp_tracker.get_all_to_convert()) == 1

    def test_refresh_converted(self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker):
        initialized_fs.create_dir("/con/ID-001")
        initialized_fs.create_dir("/con/ID-100") # overridden
        
        # test converted_mtime is "Error" if invalid conversion.log
        assert len(exp_tracker.get_all_to_process()) == 0
        exp_tracker._refresh_converted()
        all_to_process = exp_tracker.get_all_to_process()
        assert len(all_to_process) == 1
        assert all_to_process[0].props.converted_mtime == "Error"

        initialized_fs.create_file("/con/ID-001/conversion.log", contents="Conversion of ID-001 complete")
        exp_tracker._refresh_converted()
        assert exp_tracker.get_all_to_process()[0].props.converted_mtime != "Error"
        
    def test_refresh_processed(self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker):
        initialized_fs.create_dir("/con/ID-001")
        exp_tracker._refresh_converted()
        assert len(exp_tracker.get_all_to_process()) == 1
        
        initialized_fs.create_dir("/pro/ID-001")
        exp_tracker._refresh_processed()
        assert len(exp_tracker.get_all_to_process()) == 0
        
    def test_refresh_all(self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker):
        assert len(exp_tracker.get_all_experiments()) == 0
        initialized_fs.create_dir("/unc/ID-100") # overridden

        initialized_fs.create_dir("/unc/ID-001")
        exp_tracker.refresh_all()
        assert len(exp_tracker.get_all_to_convert()) == 1
        assert len(exp_tracker.get_all_to_process()) == 0
        assert len(exp_tracker.get_all_to_analyze()) == 1

        initialized_fs.create_dir("/con/ID-001")
        exp_tracker.refresh_all()
        assert len(exp_tracker.get_all_to_convert()) == 0
        assert len(exp_tracker.get_all_to_process()) == 1
        assert len(exp_tracker.get_all_to_analyze()) == 1

        initialized_fs.create_dir("/pro/ID-001")
        exp_tracker.refresh_all()
        assert len(exp_tracker.get_all_to_convert()) == 0
        assert len(exp_tracker.get_all_to_process()) == 0
        assert len(exp_tracker.get_all_to_analyze()) == 0

        assert len(exp_tracker.get_all_experiments()) == 2