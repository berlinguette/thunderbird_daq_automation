import { z } from "zod";
import { callEndpoint } from "../../api/callEndpoint";
import { Override } from "../../types/Override";

export const getOverrides = async () => {
  const overrides = await callEndpoint("/overrides");
  return z.array(Override).parse(overrides);
}

export const addOverride = async (override: Override) => {
  const response = await callEndpoint("/overrides", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(override)
  });
  return z.array(Override).parse(response);
}

export const deleteOverride = async (pattern: string) => {
  const response = await callEndpoint(`/overrides/${pattern}`, {
    method: "DELETE"
  });
  return z.array(Override).parse(response);
}