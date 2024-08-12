import { z } from "zod";

export const BaseAnalysisStepProps = z.object({
  mtime: z.number().or(z.literal("Error")),
});

export type BaseAnalysisStepProps = z.infer<typeof BaseAnalysisStepProps>;

export const AnalysisStepProps = BaseAnalysisStepProps.extend({
  overridden: z.boolean(),
});

export type AnalysisStepProps = z.infer<typeof AnalysisStepProps>;

export const ANALYSIS_STEPS_LEN = 2;

export const AnalysisSteps = z.array(z.string()).length(ANALYSIS_STEPS_LEN);

export type AnalysisSteps = z.infer<typeof AnalysisSteps>;
