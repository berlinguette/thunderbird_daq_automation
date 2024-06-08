import { getServerUrl } from "./getServerUrl";

/**
 * Calls an endpoint on the backend and returns its JSON
 * @param resource The endpoint to call - must start with `/`
 * @param options 
 * @returns 
 */
export const callEndpoint = async (
  resource: RequestInfo | URL,
  options?: RequestInit
) => {
  const response = await fetch(`${getServerUrl()}${resource}`, options);
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  return response.json();
};
