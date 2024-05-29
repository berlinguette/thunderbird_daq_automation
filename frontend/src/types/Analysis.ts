import { z } from "zod"
import { Experiment } from "./Experiment"

export const AnalysisParams = z.object({
  convert_unconverted: z.boolean().optional(),
  process_converted: z.boolean().optional(),
  force: z.boolean().optional(),
});

export type AnalysisParams = z.infer<typeof AnalysisParams>

export const AnalysisRequestParams = AnalysisParams.merge(
  z.object({ pattern: z.string().optional() })
);

export type AnalysisRequestParams = z.infer<typeof AnalysisRequestParams>

export const Analysis = z.object({
  exp: Experiment,
  params: AnalysisParams,
  stage: z.literal("convert").or(z.literal("process")),
  cancelled: z.boolean()
});

export type Analysis = z.infer<typeof Analysis>;

export const AnalysesQueue = z.object({
  current: Analysis.or(z.null()),
  queued: z.array(Analysis)
});

export type AnalysesQueue = z.infer<typeof AnalysesQueue>