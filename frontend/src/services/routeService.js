import { apiRequest } from "./api";

export function getRouteOptions() {
  return apiRequest("/api/routes/options");
}

export function generateRoute(preferences) {
  return apiRequest("/api/routes/generate", {
    method: "POST",
    body: preferences,
  });
}

export function getRouteHistory(limit = 20) {
  return apiRequest(`/api/routes/history?limit=${limit}`);
}

export function getRouteById(routeId) {
  return apiRequest(`/api/routes/${routeId}`);
}

export function getRouteMap(routeId) {
  return apiRequest(`/api/routes/${routeId}/map`);
}

export function startNavigation(routeData) {
  return apiRequest("/api/navigation/start", {
    method: "POST",
    body: routeData,
  });
}

export function getNavigationSession(sessionId) {
  return apiRequest(`/api/navigation/${sessionId}`);
}

export function updateNavigationSession(sessionId, updateData) {
  return apiRequest(`/api/navigation/${sessionId}`, {
    method: "PATCH",
    body: updateData,
  });
}

export function stopNavigation(sessionId) {
  return apiRequest(`/api/navigation/${sessionId}`, {
    method: "DELETE",
  });
}

export function getUserPreferences() {
  return apiRequest("/api/users/preferences");
}

export function saveUserPreferences(preferences) {
  return apiRequest("/api/users/preferences", {
    method: "POST",
    body: preferences,
  });
}