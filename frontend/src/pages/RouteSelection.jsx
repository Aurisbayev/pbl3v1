import React from "react";

function RouteSelection() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Route Selection</h1>

      <p className="mt-4 text-gray-700">
        This page collects the user's start location, destination, and scenic
        preferences.
      </p>

      <div className="mt-6 rounded-lg bg-white p-4 shadow">
        <label className="block font-semibold text-gray-700">
          Start Location
        </label>
        <input
          className="mt-2 w-full rounded border border-gray-300 p-2"
          placeholder="Example: Osaka Station"
        />

        <label className="mt-4 block font-semibold text-gray-700">
          Destination
        </label>
        <input
          className="mt-2 w-full rounded border border-gray-300 p-2"
          placeholder="Example: Osaka Castle"
        />

        <button className="mt-6 rounded bg-green-700 px-4 py-2 font-semibold text-white">
          Find Scenic Route
        </button>
      </div>
    </div>
  );
}

export default RouteSelection;