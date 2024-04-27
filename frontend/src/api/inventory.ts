import { InventoryFilter } from "../types/Inventory";
import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const getInventory = async (filter: InventoryFilter = undefined) => {
  const response = await fetch(`${serverUrl}/inventory${filter ? `?filter=${filter}` : ""}`);
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    return response.json();
};