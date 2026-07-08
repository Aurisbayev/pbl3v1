import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useRouteData } from "../hooks/useRouteData";
import { useRouteContext } from "../hooks/RouteContext";

function RouteSelection() {
  const navigate = useNavigate();

  const { setCurrentRoute } = useRouteContext();
  const { loading, error, handleGenerateRoute } = useRouteData();

  const [formData, setFormData] = useState({
    start_location: "",
    end_location: "",
    theme: "balanced",
    scenic_priority: 0.6,
    avoid_highways: false,
    preferred_tags: [],
  });

  const [formError, setFormError] = useState("");

  function handleChange(event) {
    const { name, value, type, checked } = event.target;

    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    if (!formData.start_location.trim()) {
      setFormError("Please enter a start location.");
      return;
    }

    if (!formData.end_location.trim()) {
      setFormError("Please enter a destination.");
      return;
    }

    const generatedRoute = await handleGenerateRoute(formData);

    if (generatedRoute) {
      setCurrentRoute(generatedRoute);
      navigate("/route-preview");
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Route Selection</h1>

      <p className="mt-4 text-gray-700">
        This page collects the user's start location, destination, and scenic
        preferences.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 rounded-lg bg-white p-4 shadow">
        <label className="block font-semibold text-gray-700">
          Start Location
        </label>
        <input
          name="start_location"
          value={formData.start_location}
          onChange={handleChange}
          className="mt-2 w-full rounded border border-gray-300 p-2"
          placeholder="Example: Osaka Station"
        />

        <label className="mt-4 block font-semibold text-gray-700">
          Destination
        </label>
        <input
          name="end_location"
          value={formData.end_location}
          onChange={handleChange}
          className="mt-2 w-full rounded border border-gray-300 p-2"
          placeholder="Example: Osaka Castle"
        />

        <label className="mt-4 block font-semibold text-gray-700">
          Route Theme
        </label>
        <select
          name="theme"
          value={formData.theme}
          onChange={handleChange}
          className="mt-2 w-full rounded border border-gray-300 p-2"
        >
          <option value="balanced">Balanced</option>
          <option value="nature">Nature</option>
          <option value="historic">Historic</option>
          <option value="waterfront">Waterfront</option>
          <option value="city">City</option>
        </select>

        <label className="mt-4 block font-semibold text-gray-700">
          Scenic Priority: {formData.scenic_priority}
        </label>
        <input
          type="range"
          name="scenic_priority"
          min="0"
          max="1"
          step="0.1"
          value={formData.scenic_priority}
          onChange={handleChange}
          className="mt-2 w-full"
        />

        <label className="mt-4 flex items-center gap-2 text-gray-700">
          <input
            type="checkbox"
            name="avoid_highways"
            checked={formData.avoid_highways}
            onChange={handleChange}
          />
          Avoid highways
        </label>

        {(formError || error) && (
          <p className="mt-4 text-red-600">
            {formError || error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="mt-6 rounded bg-green-700 px-4 py-2 font-semibold text-white disabled:bg-gray-400"
        >
          {loading ? "Finding Route..." : "Find Scenic Route"}
        </button>
      </form>
    </div>
  );
}

export default RouteSelection;
