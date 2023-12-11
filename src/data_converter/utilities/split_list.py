from typing import List, Tuple, TypeVar

T = TypeVar("T")


def split_list_by_count(to_split: List[T], count: int) -> Tuple[List[T], List[T]]:
    if count < 0:
        raise ValueError("Count must be 0 or greater")
    return to_split[:count], to_split[count:]
