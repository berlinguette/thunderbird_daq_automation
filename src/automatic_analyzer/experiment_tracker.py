from automatic_analyzer.analysis_step import AnalysisStep, AnalysisStepProps
from automatic_analyzer.experiment import Experiment
from automatic_analyzer.override_inventory import OverrideInventory


class ExperimentTracker:
    def __init__(
        self, analysis_steps: list[AnalysisStep], overrides: OverrideInventory
    ) -> None:
        self._analysis_steps = analysis_steps
        self._overrides = overrides
        self._inventory: dict[str, Experiment] = {}
        self.refresh_inventory()

    def refresh_inventory(self):
        """
        Rescans each step in the tracker's list of analysis steps
        and marks presence of the experiments in all steps
        """
        new_inventory: dict[str, Experiment] = {}
        for i, step in enumerate(self._analysis_steps):
            for id, props in step.check_experiments():
                current_exp = new_inventory.get(id, Experiment(id=id))
                override_exp = self._overrides.get_override_exp(id)

                if override_exp is not None:
                    current_step_ovr = override_exp.analysis_step_overrides[i]
                    if current_step_ovr is not None:
                        current_exp.analysis_step_props[i] = (
                            AnalysisStepProps.make_from_base(current_step_ovr, True)
                        )
                else:
                    current_exp.analysis_step_props[i] = (
                        AnalysisStepProps.make_from_base(props)
                    )

                new_inventory[id] = current_exp
        self._inventory = new_inventory

    def get_all_experiments(self) -> list[Experiment]:
        return list(self._inventory.values())

    def get_all_to_analyze(
        self, steps_to_analyze: list[bool] | None = None
    ) -> list[Experiment]:
        """
        Returns all analyzable experiments.
        For an experiment to be analyzable at a certain step,
        it must be present at that step and not present in the step following.

        The final analysis step will never be considered because
        experiments that are at this step are considered to be "done" analyzing.

        In the same vein, the first analysis step will always be analyzable, but
        this situation should never come up because it would require the first step
        of an experiment to be deleted after it has already gone through the pipeline
        """
        return [
            exp
            for exp in self._inventory.values()
            if self._is_experiment_analyzable(exp, steps_to_analyze)
        ]

    def _is_experiment_analyzable(
        self, exp: Experiment, steps_to_analyze: list[bool] | None
    ):
        for i, prop in enumerate(exp.analysis_step_props):
            if not prop.mtime_present():
                if steps_to_analyze is None:
                    return True
                # First step will always be analyzable
                # Bit of a weird edge case anyways since
                # this could only happen if you manually deleted the first step
                elif i == 0:
                    return True
                # If the experiment at the current step doesn't exist, then
                # the previous step can perform analysis - if the user
                # has allowed this step to analyze then return True
                elif steps_to_analyze[i - 1]:
                    return True
        return False
