from pathlib import Path
from typing import Dict, List, Callable

from pandas import DataFrame


def save_to_parquet(
    dfs: List[Dict[str, DataFrame]], concat_fn: Callable, data_type_key: str, full_file_path: Path
):
    wanted_dfs = [df_dict.get(data_type_key) for df_dict in dfs]
    wanted_dfs = [df for df in wanted_dfs if df is not None]
    if len(wanted_dfs) > 0:
        full_df = concat_fn(wanted_dfs, ignore_index=True)
        full_df.to_parquet(full_file_path)
