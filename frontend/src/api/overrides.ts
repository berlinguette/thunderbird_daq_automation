import { getServerUrl } from "./getServerUrl"

const serverUrl = getServerUrl();

export const getOverrides = async () => {
  const response = await fetch(`${serverUrl}/overrides`);
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }
  return response.json();
}