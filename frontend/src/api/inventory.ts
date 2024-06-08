import { getServerUrl } from "./getServerUrl"
import { callEndpoint } from "./callEndpoint";
import { Experiment } from "../types/Experiment";
import { z } from "zod";

const serverUrl = getServerUrl();

export type InventoryFilter = "to_be_converted" | "to_be_processed" | "to_be_analyzed" | undefined;

export const getInventory = async (filter: InventoryFilter = undefined) => {
  const inventory = await callEndpoint(`${serverUrl}/inventory${filter ? `?filter=${filter}` : ""}`);
  return z.array(Experiment).parse(inventory);
};