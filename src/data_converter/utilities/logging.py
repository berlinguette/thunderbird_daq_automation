from pathlib import Path


def get_conversion_logfile_path(experiment_source: Path) -> Path:
    """Gives correct conversion log file path for given experiment folder

    Parameters
    ----------
    experiment_folder : Path
        path to root folder for this experiment

    Returns
    -------
    Path
        path to experiment's conversion log file
    """
    log_filename = 'conversion.log'
    if experiment_source.is_dir():
        return experiment_source / log_filename
    else:
        return experiment_source.parent / log_filename
