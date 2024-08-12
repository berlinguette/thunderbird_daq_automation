import { z } from "zod";
import { ANALYSIS_STEPS_LEN } from "./AnalysisStep";

export const AnalysisParams = z.object({
  steps_to_analyze: z.array(z.boolean()).length(ANALYSIS_STEPS_LEN - 1),
});

export type AnalysisParams = z.infer<typeof AnalysisParams>;

export const AnalysisRequestParams = AnalysisParams.merge(
  z.object({ pattern: z.string().optional() })
);

export type AnalysisRequestParams = z.infer<typeof AnalysisRequestParams>;

export const Analysis = z.object({
  exp_id: z.string(),
  params: AnalysisParams,
  current_step: z.number().int(),
  cancelled: z.boolean(),
});

export type Analysis = z.infer<typeof Analysis>;

export const AnalysesQueue = z.object({
  current: Analysis.or(z.null()),
  queued: z.array(Analysis),
});

export type AnalysesQueue = z.infer<typeof AnalysesQueue>;
