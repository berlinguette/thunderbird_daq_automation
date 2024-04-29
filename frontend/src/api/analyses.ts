import { AnalysisParams } from "../types/Analysis";
import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const startAnalysis = async (params: AnalysisParams) => {
  const response = await fetch(`${serverUrl}/analyses`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(params)
  });
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}

export const getAnalyses = async () => {
  const response = await fetch(`${serverUrl}/analyses`);
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}