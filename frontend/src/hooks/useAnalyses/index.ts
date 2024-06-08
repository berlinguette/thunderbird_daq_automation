import { useMutation, useQuery } from "@tanstack/react-query";
import { getAnalyses, startAnalysis } from "./analyses";
import { AnalysesQueue } from "../../types/Analysis";

const useAnalyses = () => {
  const { isPending, isFetching, isError, data, error, refetch } =
    useQuery<AnalysesQueue>({
      queryKey: ["queue"],
      queryFn: getAnalyses,
      refetchInterval: 2000,
    });

  const mutation = useMutation({
    mutationFn: startAnalysis,
  });

  return {
    isPending,
    isFetching,
    isError,
    analyses: data,
    error,
    refetch,
    mutation,
  };
};

export default useAnalyses;
