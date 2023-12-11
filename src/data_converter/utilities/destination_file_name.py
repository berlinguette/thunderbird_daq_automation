from pathlib import Path
from typing import Optional


def get_destination_file_name(
    first_file: Path, index: int, data_type: Optional[str] = None
) -> str:
    source_file_name = first_file.stem
    data_type_prefix = "" if data_type is None else f"{data_type}_"
    return f"caen_{data_type_prefix}_{source_file_name}_{index}.parquet"
