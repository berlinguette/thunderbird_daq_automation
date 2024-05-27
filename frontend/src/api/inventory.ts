import { getServerUrl } from "./getServerUrl"
import { callEndpoint } from "./callEndpoint";

const serverUrl = getServerUrl();

export type InventoryFilter = "to_be_converted" | "to_be_processed" | "to_be_analyzed" | undefined;

export const getInventory = async (filter: InventoryFilter = undefined) => {
  return callEndpoint(`${serverUrl}/inventory${filter ? `?filter=${filter}` : ""}`)
};