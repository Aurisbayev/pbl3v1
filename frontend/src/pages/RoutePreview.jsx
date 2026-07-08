import React from "react";

function RoutePreview() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Route Preview</h1>

      <p className="mt-4 text-gray-700">
        This page displays the selected scenic route information.
      </p>

      <div className="mt-6 rounded-lg bg-white p-4 shadow">
        <h2 className="text-xl font-semibold text-gray-800">
          Example Scenic Route
        </h2>

        <p className="mt-2 text-gray-700">Distance: 4.5 km</p>
        <p className="text-gray-700">Estimated Time: 50 minutes</p>
        <p className="text-gray-700">Scenic Score: 85%</p>
      </div>
    </div>
  );
}

export default RoutePreview;