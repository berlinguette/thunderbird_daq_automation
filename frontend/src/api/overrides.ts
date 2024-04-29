import { Experiment } from "../types/Experiment";
import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const getOverrides = async () => {
  const response = await fetch(`${serverUrl}/overrides`);
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}

export const addOverride = async (override: Experiment) => {
  const response = await fetch(`${serverUrl}/overrides`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(override)
  });
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}

export const deleteOverride = async (pattern: string) => {
  const response = await fetch(`${serverUrl}/overrides/${pattern}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}