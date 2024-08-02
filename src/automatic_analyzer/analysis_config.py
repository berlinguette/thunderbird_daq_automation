from automatic_analyzer.env_keys import EnvConfig
from automatic_analyzer.analysis_step import (
    AnalysisStep,
    ConvertedAnalysisStep,
    UnconvertedAnalysisStep,
)
from data_converter.configuration.configuration import load_config_setup
from utilities.utilities.configuration.configuration import get_configuration


ANALYSIS_STEPS_LEN = 2


def make_analysis_steps_config(config: EnvConfig) -> list[AnalysisStep]:
    config_setup = load_config_setup()
    analysis_step_config = [
        UnconvertedAnalysisStep(
            "Unconverted Data",
            config.unconverted_data_dir,
            config.converted_data_dir,
            config_setup,
            get_configuration({}, config_setup, None),
        ),
        ConvertedAnalysisStep("Converted Data", config.converted_data_dir),
    ]
    return analysis_step_config
