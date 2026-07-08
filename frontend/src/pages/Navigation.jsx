import React from "react";
import { useNavigate } from "react-router-dom";

import { useRouteContext } from "../hooks/RouteContext";
import { useRouteData } from "../hooks/useRouteData";

function Navigation() {
  const navigate = useNavigate();

  const { navigationSession, setNavigationSession } = useRouteContext();

  const {
    loading,
    error,
    handleUpdateNavigation,
    handleStopNavigation,
  } = useRouteData();

  async function updateNavigation(action) {
    if (!navigationSession?.session_id) {
      return;
    }

    const updatedSession = await handleUpdateNavigation(
      navigationSession.session_id,
      { action }
    );

    if (updatedSession) {
      setNavigationSession(updatedSession);
    }
  }

  async function stopNavigation() {
    if (!navigationSession?.session_id) {
      return;
    }

    await handleStopNavigation(navigationSession.session_id);
    setNavigationSession(null);
    navigate("/route-selection");
  }

  if (!navigationSession) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold text-green-700">Navigation Page</h1>

        <div className="mt-6 rounded-lg bg-white p-4 shadow">
          <p className="text-gray-700">
            No navigation session has been started yet.
          </p>

          <button
            onClick={() => navigate("/route-preview")}
            className="mt-4 rounded bg-green-700 px-4 py-2 font-semibold text-white"
          >
            Back to Route Preview
          </button>
        </div>
      </div>
    );
  }

  const steps = navigationSession.steps || [];
  const currentStep = navigationSession.current_step;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Navigation Page</h1>

      <p className="mt-4 text-gray-700">
        Step-by-step navigation for the selected scenic route.
      </p>

      <div className="mt-6 rounded-lg bg-white p-4 shadow">
        <h2 className="text-xl font-semibold text-gray-800">
          Navigation Status: {navigationSession.status}
        </h2>

        {currentStep ? (
          <div className="mt-4 rounded border border-gray-200 p-4">
            <p className="font-semibold text-gray-800">
              Current Step {currentStep.step_number}
            </p>

            <p className="mt-2 text-gray-700">
              {currentStep.instruction}
            </p>

            <p className="mt-2 text-gray-600">
              Distance: {currentStep.distance_km} km
            </p>

            <p className="text-gray-600">
              Time: {currentStep.travel_time_min} min
            </p>
          </div>
        ) : (
          <p className="mt-4 text-gray-700">
            No step information is available.
          </p>
        )}

        {error && <p className="mt-4 text-red-600">{error}</p>}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            onClick={() => updateNavigation("previous_step")}
            disabled={loading}
            className="rounded bg-gray-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
          >
            Previous Step
          </button>

          <button
            onClick={() => updateNavigation("next_step")}
            disabled={loading}
            className="rounded bg-green-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
          >
            Next Step
          </button>

          <button
            onClick={() => updateNavigation("complete")}
            disabled={loading}
            className="rounded bg-blue-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
          >
            Complete
          </button>

          <button
            onClick={stopNavigation}
            disabled={loading}
            className="rounded bg-red-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
          >
            Stop Navigation
          </button>
        </div>
      </div>

      {steps.length > 0 && (
        <div className="mt-6 rounded-lg bg-white p-4 shadow">
          <h2 className="text-xl font-semibold text-gray-800">All Steps</h2>

          <ol className="mt-3 list-decimal space-y-2 pl-6 text-gray-700">
            {steps.map((step) => (
              <li key={step.step_number}>
                {step.instruction}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export default Navigation;
