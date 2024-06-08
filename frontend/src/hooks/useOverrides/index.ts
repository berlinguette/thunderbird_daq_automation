import { useMutation, useQuery } from "@tanstack/react-query";
import { addOverride, deleteOverride, getOverrides } from "./overrides";

const useOverrides = () => {
  const { isPending, isError, data, error, refetch } = useQuery({
    queryKey: ["overrides"],
    queryFn: getOverrides,
    staleTime: Infinity,
  });
  const deleteOvrMutation = useMutation({
    mutationKey: ["overrides"],
    mutationFn: deleteOverride,
  });
  const addOvrMutation = useMutation({
    mutationKey: ["overrides"],
    mutationFn: addOverride,
  });

  return {
    isPending,
    isError,
    overrides: data,
    error,
    refetchOverrides: refetch,
    deleteOvrMutation,
    addOvrMutation,
  };
};

export default useOverrides;
