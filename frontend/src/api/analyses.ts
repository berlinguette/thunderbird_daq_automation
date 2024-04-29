import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export type AnalysisFilter = {
  convert_unconverted?: boolean|undefined,
  process_converted?: boolean|undefined,
  pattern?: string|undefined,
  force?: boolean|undefined
}

export const startAnalysis = async (params: AnalysisFilter) => {
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