import { useQuery } from "@tanstack/react-query";
import { callEndpoint } from "../../api/callEndpoint";
import { AnalysisSteps } from "../../types/AnalysisStep";

export const useAnalysisSteps = () => {
  const { isPending, isFetching, isError, data, error, refetch } =
    useQuery<AnalysisSteps>({
      queryKey: ["analysis_steps"],
      queryFn: getAnalysisSteps,
    });

  return {
    isPending,
    isFetching,
    isError,
    steps: data,
    error,
    refetch,
  };
};

const getAnalysisSteps = async () => {
  const analyses = await callEndpoint("/analysis_steps");
  return AnalysisSteps.parse(analyses);
};
