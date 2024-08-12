import { z } from "zod";
import { AnalysisStepProps } from "./AnalysisStep";

export const Experiment = z.object({
  id: z.string(),
  analysis_step_props: z.array(AnalysisStepProps),
});

export type Experiment = z.infer<typeof Experiment>;
