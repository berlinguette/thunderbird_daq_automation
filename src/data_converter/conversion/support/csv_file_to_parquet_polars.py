import re
from pathlib import Path

import polars as pl


DELIMITER = ';'
END_NUMBER_PATTERN = r'^(.*_)(\d+)$'

def query_csv(
        source_file: Path,
        headers: list[str],
) -> pl.LazyFrame:
    line_skip_count = 1 if _has_header_line(source_file) else 0

    new_dtypes = [pl.String for _ in headers]
    lf = pl.scan_csv(
        source_file,
        has_header=False,
        separator=DELIMITER,
        skip_lines=line_skip_count,
        schema_overrides=new_dtypes,
        new_columns=headers
    )
    return lf


# def _get_split_cols(
#     headers: list[str],
#     total_cols: int
# ) -> tuple[list[str], list[str]]:
#     psd_cols = [col for col in headers if col != SAMPLES_COL_NAME]
#     signal_cols = [str(n) for n
#                    in range(total_cols - len(psd_cols))]
#     return psd_cols, signal_cols


def _has_header_line(source_file: Path) -> bool:
    return re.match(END_NUMBER_PATTERN, source_file.stem) is None
