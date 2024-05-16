from automatic_analyzer.experiment_inventory import ExperimentProperties


def make_experiment_props():
    return ExperimentProperties(
        unconverted_mtime=0, converted_mtime=0, processed_mtime=0, overridden=False
    )