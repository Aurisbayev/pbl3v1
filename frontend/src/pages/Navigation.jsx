import React from "react";

function Navigation() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-green-700">Navigation Page</h1>

      <p className="mt-4 text-gray-700">
        This page will show step-by-step navigation for the selected scenic route.
      </p>

      <div className="mt-6 rounded-lg bg-white p-4 shadow">
        <h2 className="text-xl font-semibold text-gray-800">Example Steps</h2>

        <ol className="mt-3 list-decimal space-y-2 pl-6 text-gray-700">
          <li>Start from your current location.</li>
          <li>Walk toward the nearest scenic path.</li>
          <li>Continue through parks, rivers, or historical areas.</li>
          <li>Arrive at your destination.</li>
        </ol>
      </div>
    </div>
  );
}

export default Navigation;
