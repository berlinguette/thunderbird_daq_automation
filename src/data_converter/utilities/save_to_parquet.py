from pathlib import Path
from typing import Dict, List, Literal

import pandas as pd
import modin.pandas as modin_pd


def save_to_parquet(
    dfs: List[Dict[str, pd.DataFrame]], concat_fn_type: Literal['pandas', 'modin'], data_type_key: str, full_file_path: Path
):
    wanted_dfs = [df_dict.get(data_type_key) for df_dict in dfs]
    wanted_dfs = [df for df in wanted_dfs if df is not None]
    if len(wanted_dfs) > 0:
        if concat_fn_type == "pandas":
            full_df = pd.concat(wanted_dfs, ignore_index=True)
        elif concat_fn_type == "modin":
            full_df = modin_pd.concat(wanted_dfs, ignore_index=True)
        else:
            raise ValueError(f"Invalid concat_fn_type {concat_fn_type}")
        full_df.to_parquet(full_file_path)
