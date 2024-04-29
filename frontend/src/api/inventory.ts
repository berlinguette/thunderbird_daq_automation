import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export type InventoryFilter = "to_be_converted" | "to_be_processed" | "to_be_analyzed" | undefined;

export const getInventory = async (filter: InventoryFilter = undefined) => {
  const response = await fetch(`${serverUrl}/inventory${filter ? `?filter=${filter}` : ""}`);
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    return response.json();
};