export type Experiment = {
  id: string,
  props: {
    unconverted_mtime: Date | -1,
    converted_mtime: Date | -1,
    processed_mtime: Date | -1,
    overridden: boolean
  }
};