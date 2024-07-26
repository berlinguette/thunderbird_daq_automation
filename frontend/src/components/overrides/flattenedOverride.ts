import { Experiment } from "../../types/Experiment";

/**
 * Flattens all keys of an incoming override into the top level -
 * allows us to work with all properties the same way in `<Override />`
 */
export type FlattenedOverride = {
  pattern: string;
  unconverted_mtime: string;
  converted_mtime: string;
  processed_mtime: string;
};

export const flattenOverride = (ovr: Experiment): FlattenedOverride => {
  const unc = new Date(ovr.props.unconverted_mtime);
  const conv = new Date(ovr.props.converted_mtime);
  const proc = new Date(ovr.props.processed_mtime);
  return {
    pattern: ovr.id,
    unconverted_mtime:
      unc.valueOf() == 0 ? "0" : new Date(unc).toLocaleString(),
    converted_mtime:
      conv.valueOf() == 0 ? "0" : new Date(conv).toLocaleString(),
    processed_mtime:
      proc.valueOf() == 0 ? "0" : new Date(proc).toLocaleString(),
  };
};

export const unflattenOverride = (ovr: FlattenedOverride): Experiment => {
  return {
    id: ovr.pattern,
    props: {
      unconverted_mtime:
        ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.unconverted_mtime),
      converted_mtime:
        ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.converted_mtime),
      processed_mtime:
        ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.processed_mtime),
      overridden: true,
    },
  };
};