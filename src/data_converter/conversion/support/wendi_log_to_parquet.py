import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from utilities.utilities.logging_helpers.setup_logger import (Messenger,
                                                              cleanup_logger,
                                                              setup_logger)
from utilities.utilities.timing import Timer

logger = logging.getLogger('wendi_log_to_parquet')
messenger = Messenger(logger)
log_only_messenger = Messenger(logger, on_screen=False)


def convert_wendi_log_to_parquet(
    source_file: Path, destination: Path, logfile_path: Path
):
    setup_logger(logger, logfile_path)
    log_only_messenger.debug(
        f"Starting wendi log conversion in {source_file.name}")
    timer = Timer(start_now=True)

    try:
        df = pd.read_csv(
            source_file,
            sep='\t',
            header=8,
            # TODO warn on bad lines, catch warnings and log
            on_bad_lines='skip'
        )
        df.to_parquet(destination)
    except (MemoryError, IOError) as err:
        logger.exception(err)
        tqdm.write(
            f"Conversion failed for {source_file.name}. " +
            "See conversion.log for details"
        )

    exec_time = timer.stop_timer()
    formatted_time = timer.format_elapsed_time(exec_time, decimals=4)
    messenger.info(f"WENDI log processed")
    log_only_messenger.debug(f"Elapsed time: {formatted_time}")
    cleanup_logger(logger)
