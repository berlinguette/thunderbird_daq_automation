import { AnalysesQueue, AnalysisRequestParams } from "../types/Analysis";
import { callEndpoint } from "./callEndpoint";
import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const startAnalysis = async (params: AnalysisRequestParams) => {
  const response = await callEndpoint(`${serverUrl}/analyses`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(params)
  });
  return AnalysesQueue.parse(response);
}

export const getAnalyses = async () => {
  const analyses = await callEndpoint(`${serverUrl}/analyses`);
  return AnalysesQueue.parse(analyses);
}