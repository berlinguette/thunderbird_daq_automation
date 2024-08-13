import { Override } from "../../types/Override";

/** Override with less strict typing rules for mtimes, used for input boxes */
export type UnstrictOverride = {
  pattern: string;
  analysis_step_overrides: {
    mtime: string;
  }[];
};

export const makeUnstrictOverride = (override: Override): UnstrictOverride => {
  return {
    pattern: override.pattern,
    analysis_step_overrides: override.analysis_step_overrides.map((val) => {
      if (!val) return { mtime: "" };
      return {
        mtime: getUserFriendlyMTime(val.mtime),
      };
    }),
  };
};

const getUserFriendlyMTime = (mtime: number | "Error") => {
  if (mtime == "Error" || mtime == 0) return String(mtime);
  else return new Date(mtime).toLocaleString();
};

export const makeStrictOverride = (
  unstrictOverride: UnstrictOverride
): Override => {
  return {
    pattern: unstrictOverride.pattern,
    analysis_step_overrides: unstrictOverride.analysis_step_overrides.map(
      ({ mtime }) => getProperTypedMTime(mtime)
    ),
  };
};

const getProperTypedMTime = (
  mtime: string
): { mtime: number | "Error" } | undefined => {
  if (mtime === "") return undefined;
  else if (mtime === "Error") return { mtime };
  else if (mtime === "0") return { mtime: 0 };
  else return { mtime: Date.parse(mtime) };
};
