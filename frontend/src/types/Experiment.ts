export type ExperimentProps = {
  unconverted_mtime: number | "Error",
  converted_mtime: number | "Error",
  processed_mtime: number | "Error",
  overridden: boolean
};

export type Experiment = {
  id: string,
  props: ExperimentProps
};