import { useState } from "react";

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function request(apiFunction, ...args) {
    setLoading(true);
    setError("");

    try {
      const response = await apiFunction(...args);
      return response;
    } catch (err) {
      setError(err.message || "Request failed.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  function clearError() {
    setError("");
  }

  return {
    loading,
    error,
    request,
    clearError,
    setError,
  };
}