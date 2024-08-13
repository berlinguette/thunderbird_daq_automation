import { z } from "zod";
import { ANALYSIS_STEPS_LEN, BaseAnalysisStepProps } from "./AnalysisStep";

export const Override = z.object({
  pattern: z.string(),
  analysis_step_overrides: z
    .array(BaseAnalysisStepProps.or(z.undefined()))
    .length(ANALYSIS_STEPS_LEN),
});

export type Override = z.infer<typeof Override>;
