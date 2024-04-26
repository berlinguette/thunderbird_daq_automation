export type ExperimentProps = {
  unconverted_mtime: number,
  converted_mtime: number,
  processed_mtime: number,
  overridden: boolean
};

export type Experiment = {
  id: string,
  props: ExperimentProps
};