import { useQuery } from "@tanstack/react-query";
import { getServerUrl } from "../../api/getServerUrl";
import { callEndpoint } from "../../api/callEndpoint";
import { Experiment } from "../../types/Experiment";
import { z } from "zod";

const serverUrl = getServerUrl();

export type InventoryFilter = "to_be_converted" | "to_be_processed" | "to_be_analyzed" | undefined;

const getInventory = async (filter: InventoryFilter = undefined) => {
  const inventory = await callEndpoint(`${serverUrl}/inventory${filter ? `?filter=${filter}` : ""}`);
  return z.array(Experiment).parse(inventory);
};

const useInventory = (filter: InventoryFilter) => {
  const { isPending, isFetching, isError, data, error, refetch } = useQuery({
    queryKey: ["inventory", filter],
    queryFn: () => getInventory(filter),
  });

  return {
    isPending,
    isFetching,
    isError,
    inventory: data,
    error,
    refetchInventory: refetch,
  };
};

export default useInventory;
