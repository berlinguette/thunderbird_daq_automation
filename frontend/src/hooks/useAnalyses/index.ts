import { useMutation, useQuery } from "@tanstack/react-query";
import { getAnalyses, startAnalysis } from "./analyses";
import { AnalysesQueue } from "../../types/Analysis";

export const useGetAnalyses = () => {
  const { isPending, isFetching, isError, data, error, refetch } =
    useQuery<AnalysesQueue>({
      queryKey: ["queue"],
      queryFn: getAnalyses,
      refetchInterval: 2000,
    });

  return {
    isPending,
    isFetching,
    isError,
    analyses: data,
    error,
    refetch,
  };
};

export const useMutateAnalyses = () => {
  const mutation = useMutation({
    mutationFn: startAnalysis,
  });
  return { mutation };
};
