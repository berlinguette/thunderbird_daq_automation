from typing import Literal

import pytest

from automatic_analyzer.experiment_inventory import ExperimentProperties


def make_experiment_props(
    unc_mtime: float | Literal["Error"] = 0,
    con_mtime: float | Literal["Error"] = 0,
    pro_mtime: float | Literal["Error"] = 0,
    overridden: bool = False,
):
    return ExperimentProperties(
        unconverted_mtime=unc_mtime,
        converted_mtime=con_mtime,
        processed_mtime=pro_mtime,
        overridden=overridden,
    )


@pytest.fixture
def experiment_props():
    return make_experiment_props()
