from pydantic import BaseModel, Field, validator
from automatic_analyzer.analysis_config import ANALYSIS_STEPS_LEN
from automatic_analyzer.analysis_step import AnalysisStepProps


class Experiment(BaseModel):
    """Represents a single experiment in the data automation pipeline"""

    id: str
    analysis_step_props: list[AnalysisStepProps] = Field(
        default_factory=lambda: [AnalysisStepProps(mtime=-1)] * ANALYSIS_STEPS_LEN
    )
    """
    List of analysis props (ex. mtime) gathered by each analysis step
    in the current configuration
    """

    @validator("analysis_step_props")
    def proper_steps_len(cls, v):
        if len(v) != ANALYSIS_STEPS_LEN:
            raise ValueError("analysis_step_props list has invalid length")
        return v
