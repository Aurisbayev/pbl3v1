const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5173";

export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  if (options.body !== undefined) {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(url, config);

    let data = null;

    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const message =
        data?.message ||
        data?.error ||
        data?.errors?.server ||
        "Request failed";

      throw new Error(message);
    }

    return data;
  } catch (error) {
    if (error.message === "Failed to fetch") {
      throw new Error("Backend is unavailable. Make sure Flask is running on port 5000.");
    }

    throw new Error(error.message || "Something went wrong.");
  }
}

export function getResponseData(response) {
  return response?.data ?? response;
}
