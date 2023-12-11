from typing import Dict

from pandas import DataFrame


def get_df_total_mem_usage(df: DataFrame) -> float:
    # returns mem usage in MB
    mem_usage = df.memory_usage(deep=True)
    return float(mem_usage.sum(skipna=True)) / (1024 * 1024)


def get_df_dict_mem_usage(df_dict: Dict[str, DataFrame]) -> float:
    df_usage = [get_df_total_mem_usage(df) for df in df_dict.values()]
    return sum(df_usage)
