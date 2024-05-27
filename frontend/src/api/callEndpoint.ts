export const callEndpoint = async (resource: RequestInfo | URL, options?: RequestInit) => {
    const response = await fetch(resource , options);
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
}