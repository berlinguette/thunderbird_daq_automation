import { Experiment } from "./Experiment"

export type AnalysisParams = {
  convert_unconverted?: boolean|undefined,
  process_converted?: boolean|undefined,
  pattern?: string|undefined,
  force?: boolean|undefined
}

export type Analysis = {
  exp: Experiment,
  params: AnalysisParams,
  stage: "convert" | "process",
  cancelled: boolean
}