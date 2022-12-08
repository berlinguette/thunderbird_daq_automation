from pathlib import Path

def get_conversion_logfile_path(experiment_folder: Path) -> Path:
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
    return experiment_folder / log_filename