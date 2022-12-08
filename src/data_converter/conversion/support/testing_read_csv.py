from pathlib import Path
import modin.pandas as modin_pd
import dask.dataframe as dd
import pandas as pd
import re

    
def pandas_csv_read(datafile: Path, col_names: list[str]):
    return gen_csv_read(datafile, col_names, pd.read_csv)


def dask_csv_read(datafile: Path, col_names: list[str]):
    return gen_csv_read(datafile, col_names, dd.read_csv)
    

def modin_csv_read(datafile: Path, col_names: list[str]):
    return gen_csv_read(datafile, col_names, modin_pd.read_csv)


def gen_csv_read(datafile: Path, col_names: list[str], reader):
    has_header_match = re.match(r'(.*_)(\d+)', datafile.stem)
    skiprows = 1 if has_header_match is not None else 0
    header = 0 if has_header_match is not None else None
    return reader(
        datafile,
        sep=';',
        header=header,
        skiprows=skiprows,
        dtype=str,
        on_bad_lines='warn'
    )


def csv_list_read(files: list[Path], col_names: list[str]):
    for file in files:
        print(f"-- Testing {file.name} --")
        
        print("- Pandas -")
        df = pandas_csv_read(file, col_names)
        print(df.head())
        del(df)
        
        print("- Dask -")
        df = pandas_csv_read(file, col_names)
        print(df.head())
        del(df)
        
        print("- Modin -")
        df = pandas_csv_read(file, col_names)
        print(df.head())
        del(df)
