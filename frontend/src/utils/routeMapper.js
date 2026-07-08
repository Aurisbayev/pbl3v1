import { formatDistance, formatTime, formatScenicScore } from "./formatters";

export function mapRouteResponse(routeData) {
  if (!routeData) {
    return null;
  }

  const route = routeData.route || routeData;
  const summary = route.summary || routeData.summary || {};

  const distance =
    summary.distance_km ??
    route.distance_km ??
    route.total_distance_km ??
    0;

  const travelTime =
    summary.travel_time_min ??
    route.travel_time_min ??
    route.total_travel_time_min ??
    0;

  const scenicScore =
    summary.scenic_score ??
    route.scenic_score ??
    route.average_scenic_score ??
    0;

  return {
    id: route.id || route.route_id || routeData.id || null,
    name: route.name || route.title || "Generated Scenic Route",
    summary,
    distance,
    travelTime,
    scenicScore,
    distanceText: formatDistance(distance),
    travelTimeText: formatTime(travelTime),
    scenicScoreText: formatScenicScore(scenicScore),
    segments: route.segments || [],
    coordinates: route.coordinates || route.path || [],
    map: routeData.map || route.map || null,
    raw: routeData,
  };
}

export function mapHistoryResponse(historyData) {
  const items = historyData?.items || historyData?.routes || historyData || [];

  if (!Array.isArray(items)) {
    return [];
  }

  return items.map(mapRouteResponse);
}