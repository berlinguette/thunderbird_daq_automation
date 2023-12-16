from typing import Dict, Union

from pandas import DataFrame
from modin.pandas import DataFrame as ModinDataFrame


def get_df_total_mem_usage(df: Union[DataFrame, ModinDataFrame], index: bool = True) -> float:
    # returns mem usage in MB
    mem_usage = df.memory_usage(deep=True, index=index)
    return float(mem_usage.sum(skipna=True)) / (1024 * 1024)


def get_df_dict_mem_usage(df_dict: Dict[str, DataFrame], index: bool = True) -> float:
    df_usage = [get_df_total_mem_usage(df, index=index) for df in df_dict.values()]
    return sum(df_usage)
