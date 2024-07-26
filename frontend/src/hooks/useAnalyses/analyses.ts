import { callEndpoint } from "../../api/callEndpoint";
import { AnalysesQueue, AnalysisRequestParams } from "../../types/Analysis";

export const startAnalysis = async (params: AnalysisRequestParams) => {
  const response = await callEndpoint("/analyses", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  });
  return AnalysesQueue.parse(response);
};

export const getAnalyses = async () => {
  const analyses = await callEndpoint("/analyses");
  return AnalysesQueue.parse(analyses);
};
