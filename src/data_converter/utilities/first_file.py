import re
from pathlib import Path
from typing import List


def get_first_source_file(source_files: List[Path], pattern: str):
    first_file = [f for f in source_files if re.match(pattern, f.stem) is None]
    if len(first_file) == 0:
        raise ValueError("Could not find first source file")
    return first_file[0]
