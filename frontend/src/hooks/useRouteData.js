import { useState } from "react";
import { getResponseData } from "../services/api";
import {
  generateRoute,
  getRouteOptions,
  getRouteHistory,
  startNavigation,
  getNavigationSession,
  updateNavigationSession,
  stopNavigation,
  getUserPreferences,
  saveUserPreferences,
} from "../services/routeService";
import { mapRouteResponse, mapHistoryResponse } from "../utils/routeMapper";
import { useApi } from "./useApi";

export function useRouteData() {
  const [routeOptions, setRouteOptions] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [currentRoute, setCurrentRoute] = useState(null);
  const [routeHistory, setRouteHistory] = useState([]);
  const [navigationSession, setNavigationSession] = useState(null);

  const { loading, error, request, clearError } = useApi();

  async function loadRouteOptions() {
    const response = await request(getRouteOptions);
    const data = getResponseData(response);

    if (data) {
      setRouteOptions(data);
    }

    return data;
  }

  async function loadUserPreferences() {
    const response = await request(getUserPreferences);
    const data = getResponseData(response);

    if (data) {
      setPreferences(data);
    }

    return data;
  }

  async function savePreferences(newPreferences) {
    const response = await request(saveUserPreferences, newPreferences);
    const data = getResponseData(response);

    if (data) {
      setPreferences(data);
    }

    return data;
  }

  async function handleGenerateRoute(routePreferences) {
    const response = await request(generateRoute, routePreferences);
    const data = getResponseData(response);

    if (data) {
      const mappedRoute = mapRouteResponse(data);
      setCurrentRoute(mappedRoute);
      return mappedRoute;
    }

    return null;
  }

  async function loadRouteHistory(limit = 20) {
    const response = await request(getRouteHistory, limit);
    const data = getResponseData(response);

    if (data) {
      const mappedHistory = mapHistoryResponse(data);
      setRouteHistory(mappedHistory);
      return mappedHistory;
    }

    return [];
  }

  async function handleStartNavigation(routeOrRouteId) {
    let body;

    if (typeof routeOrRouteId === "number" || typeof routeOrRouteId === "string") {
      body = {
        route_id: routeOrRouteId,
      };
    } else {
      body = {
        route: routeOrRouteId?.raw?.route || routeOrRouteId?.raw || routeOrRouteId,
      };
    }

    const response = await request(startNavigation, body);
    const data = getResponseData(response);

    if (data) {
      setNavigationSession(data);
      return data;
    }

    return null;
  }

  async function loadNavigationSession(sessionId) {
    const response = await request(getNavigationSession, sessionId);
    const data = getResponseData(response);

    if (data) {
      setNavigationSession(data);
    }

    return data;
  }

  async function handleUpdateNavigation(sessionId, updateData) {
    const response = await request(updateNavigationSession, sessionId, updateData);
    const data = getResponseData(response);

    if (data) {
      setNavigationSession(data);
    }

    return data;
  }

  async function handleStopNavigation(sessionId) {
    const response = await request(stopNavigation, sessionId);
    const data = getResponseData(response);

    if (data) {
      setNavigationSession(null);
    }

    return data;
  }

  return {
    routeOptions,
    preferences,
    currentRoute,
    routeHistory,
    navigationSession,
    loading,
    error,
    clearError,
    loadRouteOptions,
    loadUserPreferences,
    savePreferences,
    handleGenerateRoute,
    loadRouteHistory,
    handleStartNavigation,
    loadNavigationSession,
    handleUpdateNavigation,
    handleStopNavigation,
    setCurrentRoute,
  };
}