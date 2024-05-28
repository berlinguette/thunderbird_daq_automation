import { Experiment } from "../types/Experiment";
import { getServerUrl } from "./getServerUrl"
import { callEndpoint } from "./callEndpoint";

const serverUrl = getServerUrl();

export const getOverrides = async () => {
  return callEndpoint(`${serverUrl}/overrides`);
}

export const addOverride = async (override: Experiment) => {
  return callEndpoint(`${serverUrl}/overrides`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(override)
  });
}

export const deleteOverride = async (pattern: string) => {
  return callEndpoint(`${serverUrl}/overrides/${pattern}`, {
    method: "DELETE"
  });
}