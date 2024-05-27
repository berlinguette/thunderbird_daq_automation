import { AnalysisRequestParams } from "../types/Analysis";
import { callEndpoint } from "./callEndpoint";
import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const startAnalysis = async (params: AnalysisRequestParams) => {
  return callEndpoint(`${serverUrl}/analyses`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(params)
  });
}

export const getAnalyses = async () => {
  return callEndpoint(`${serverUrl}/analyses`);
}