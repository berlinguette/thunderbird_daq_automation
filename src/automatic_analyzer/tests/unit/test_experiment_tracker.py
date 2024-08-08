from automatic_analyzer.experiment_tracker import ExperimentTracker
from pyfakefs.fake_filesystem import FakeFilesystem


class TestExperimentTracker:
    def test_should_find_new_unconverted_experiment_with_and_without_error(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        """Test that unconverted experiments are detected"""
        initialized_fs.create_dir("/unc/ID-001")
        initialized_fs.create_dir("/unc/ID-100")  # overridden

        # test converted_mtime is "Error" if invalid no run.info
        assert len(exp_tracker.get_all_to_analyze([True, False])) == 0
        exp_tracker.refresh_inventory()
        assert len(exp_tracker.get_all_to_analyze([True, False])) == 0

        initialized_fs.create_file("/unc/ID-001/run.info")
        exp_tracker.refresh_inventory()
        assert len(exp_tracker.get_all_to_analyze([True, False])) == 1

    def test_should_find_new_converted_experiment_with_and_without_error(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        initialized_fs.create_dir("/con/ID-001")
        initialized_fs.create_dir("/con/ID-100")  # overridden

        # test converted_mtime is "Error" if invalid conversion.log
        assert len(exp_tracker.get_all_to_analyze([True, True])) == 0
        exp_tracker.refresh_inventory()
        assert len(exp_tracker.get_all_to_analyze([True, True])) == 0

        exp = exp_tracker.get("ID-001")
        assert exp is not None
        assert exp.analysis_step_props[1].mtime == "Error"

        initialized_fs.create_file(
            "/con/ID-001/conversion.log", contents="Conversion of ID-001 complete"
        )
        exp_tracker.refresh_inventory()
        exp = exp_tracker.get("ID-001")
        assert exp is not None
        assert exp.analysis_step_props[1].mtime_present()
    
    def test_should_override_experiment_props(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        initialized_fs.create_dir("/con/ID-100")  # overridden

        # test converted_mtime is "Error" if invalid conversion.log
        assert len(exp_tracker.get_all_experiments()) == 0
        exp_tracker.refresh_inventory()
        experiments = exp_tracker.get_all_experiments()
        assert len(experiments) == 1
        for prop in experiments[0].analysis_step_props:
            assert prop.mtime == 0
            assert prop.overridden
