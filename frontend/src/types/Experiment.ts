import { z } from "zod";

export const ExperimentProps = z.object({
  unconverted_mtime: z.number().or(z.literal("Error")),
  converted_mtime: z.number().or(z.literal("Error")),
  processed_mtime: z.number().or(z.literal("Error")),
  overridden: z.boolean()
})

export type ExperimentProps = z.infer<typeof ExperimentProps>;

export const Experiment = z.object({
  id: z.string(),
  props: ExperimentProps
})

export type Experiment = z.infer<typeof Experiment>