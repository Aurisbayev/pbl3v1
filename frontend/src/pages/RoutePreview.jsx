import React from "react";
import { useNavigate } from "react-router-dom";

import { useRouteContext } from "../hooks/RouteContext";
import { useRouteData } from "../hooks/useRouteData";

function RoutePreview() {
  const navigate = useNavigate();

  const { currentRoute, setNavigationSession } = useRouteContext();
  const { loading, error, handleStartNavigation } = useRouteData();

  async function startNavigation() {
    if (!currentRoute) {
      return;
    }

    const session = await handleStartNavigation(currentRoute);

    if (session) {
      setNavigationSession(session);
      navigate("/navigation");
    }
  }

  if (!currentRoute) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold text-green-700">Route Preview</h1>

        <div className="mt-6 rounded-lg bg-white p-4 shadow">
          <p className="text-gray-700">
            No route has been generated yet.
          </p>

          <button
            onClick={() => navigate("/route-selection")}
            className="mt-4 rounded bg-green-700 px-4 py-2 font-semibold text-white"
          >
            Go to Route Selection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Route Preview</h1>

      <p className="mt-4 text-gray-700">
        This page displays the selected scenic route information.
      </p>

      <div className="mt-6 rounded-lg bg-white p-4 shadow">
        <h2 className="text-xl font-semibold text-gray-800">
          {currentRoute.name}
        </h2>

        <p className="mt-2 text-gray-700">
          Distance: {currentRoute.distanceText}
        </p>

        <p className="text-gray-700">
          Estimated Time: {currentRoute.travelTimeText}
        </p>

        <p className="text-gray-700">
          Scenic Score: {currentRoute.scenicScoreText}
        </p>

        {currentRoute.segments && currentRoute.segments.length > 0 && (
          <div className="mt-4">
            <h3 className="font-semibold text-gray-800">Route Segments</h3>

            <ol className="mt-2 list-decimal space-y-2 pl-6 text-gray-700">
              {currentRoute.segments.map((segment, index) => (
                <li key={index}>
                  {segment.road_name || "Scenic path"} —{" "}
                  {segment.distance_km || 0} km
                </li>
              ))}
            </ol>
          </div>
        )}

        {error && <p className="mt-4 text-red-600">{error}</p>}

        <button
          onClick={startNavigation}
          disabled={loading}
          className="mt-6 rounded bg-green-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
        >
          {loading ? "Starting Navigation..." : "Start Navigation"}
        </button>
      </div>
    </div>
  );
}

export default RoutePreview;
