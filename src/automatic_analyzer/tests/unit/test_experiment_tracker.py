from automatic_analyzer.experiment_tracker import ExperimentTracker
from pyfakefs.fake_filesystem import FakeFilesystem


class TestExperimentTracker:
    def test_should_find_new_unconverted_experiment(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        initialized_fs.create_dir("/unc/ID-001")
        initialized_fs.create_dir("/unc/ID-100")  # overridden

        assert len(exp_tracker.get_all_to_convert()) == 0
        exp_tracker._refresh_unconverted()
        assert len(exp_tracker.get_all_to_convert()) == 1

    def test_should_find_new_converted_experiment_with_and_without_error(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        initialized_fs.create_dir("/con/ID-001")
        initialized_fs.create_dir("/con/ID-100")  # overridden

        # test converted_mtime is "Error" if invalid conversion.log
        assert len(exp_tracker.get_all_to_process()) == 0
        exp_tracker._refresh_converted()
        all_to_process = exp_tracker.get_all_to_process()
        assert len(all_to_process) == 1
        assert all_to_process[0].props.converted_mtime == "Error"

        initialized_fs.create_file(
            "/con/ID-001/conversion.log", contents="Conversion of ID-001 complete"
        )
        exp_tracker._refresh_converted()
        assert exp_tracker.get_all_to_process()[0].props.converted_mtime != "Error"

    def test_should_find_new_processed_experiment_with_and_without_error(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        initialized_fs.create_dir("/pro/ID-001")
        exp_tracker._refresh_processed()
        all_experiments = exp_tracker.get_all_experiments()
        assert len(all_experiments) == 1
        assert all_experiments[0].props.processed_mtime == "Error"

        initialized_fs.create_file("/pro/ID-001/output.csv")
        exp_tracker._refresh_processed()
        assert exp_tracker.get_all_experiments()[0].props.processed_mtime != "Error"

    def test_should_find_unconverted_then_converted_then_processed_as_added(
        self, initialized_fs: FakeFilesystem, exp_tracker: ExperimentTracker
    ):
        assert len(exp_tracker.get_all_experiments()) == 0
        initialized_fs.create_dir("/unc/ID-100")  # overridden

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
