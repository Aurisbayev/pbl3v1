import React, { useState } from "react";
import mapImage from "../assets/londonimage.jpeg";

function Home() {
  const [zoom, setZoom] = useState(13);
  const [destination, setDestination] = useState("");
  const [searchedDestination, setSearchedDestination] = useState("");
  const [activeTool, setActiveTool] = useState("None");
  const [showLayers, setShowLayers] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  const scale = getScaleFromZoom(zoom);

  function handleSearch(event) {
    event.preventDefault();

    if (destination.trim() === "") {
      setSearchedDestination("No destination entered");
      return;
    }

    setSearchedDestination(destination);
    setActiveTool("Search");
  }

  function zoomIn() {
    setZoom((currentZoom) => Math.min(currentZoom + 1, 18));
    setActiveTool("Zoom In");
  }

  function zoomOut() {
    setZoom((currentZoom) => Math.max(currentZoom - 1, 10));
    setActiveTool("Zoom Out");
  }

  function handleLocate() {
    setActiveTool("Current Location");
  }

  function handleLayers() {
    setShowLayers(!showLayers);
    setActiveTool("Map Layers");
  }

  function handleInfo() {
    setShowInfo(!showInfo);
    setActiveTool("Map Information");
  }

  function handleHelp() {
    setActiveTool("Help");
    alert(
      "Use the search box to enter a destination. Use + and - to change zoom. The ruler changes based on zoom level."
    );
  }

  return (
    <div className="relative h-[calc(100vh-4rem)] overflow-hidden bg-gray-200">
      <div className="absolute inset-0 bg-gray-300">
        <img
          src={mapImage}
          alt="London map placeholder"
          className="h-full w-full object-cover"
        />

        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white/90 px-6 py-4 text-center shadow-lg">
          <h1 className="text-2xl font-bold text-gray-800">
            Map Overview Placeholder
          </h1>

          <p className="mt-2 text-gray-600">
            This image is a temporary placeholder. Later, it can be replaced
            with a real map service.
          </p>

          <div className="mt-4 rounded-lg bg-green-100 p-3 text-green-800">
            <p className="font-semibold">Current Zoom Level: {zoom}</p>
            <p>Current Tool: {activeTool}</p>
            {searchedDestination && <p>Destination: {searchedDestination}</p>}
          </div>
        </div>
      </div>

      <form
        onSubmit={handleSearch}
        className="absolute left-4 top-4 z-20 flex w-[380px] max-w-[90%] overflow-hidden rounded-lg shadow-lg"
      >
        <input
          type="text"
          value={destination}
          onChange={(event) => setDestination(event.target.value)}
          placeholder="Search for a destination"
          className="w-full bg-gray-900 px-4 py-3 text-white outline-none placeholder:text-gray-400"
        />

        <button
          type="submit"
          className="bg-blue-600 px-5 text-white hover:bg-blue-700"
        >
          Search
        </button>
      </form>

      <div className="absolute right-4 top-4 z-20 flex flex-col overflow-hidden rounded-lg shadow-lg">
        <button
          onClick={zoomIn}
          className="border-b border-gray-600 bg-gray-900 px-5 py-3 text-2xl font-bold text-white hover:bg-gray-700"
        >
          +
        </button>

        <button
          onClick={zoomOut}
          className="bg-gray-900 px-5 py-3 text-2xl font-bold text-white hover:bg-gray-700"
        >
          −
        </button>
      </div>

      <div className="absolute right-4 top-36 z-20 flex flex-col overflow-hidden rounded-lg shadow-lg">
        <button
          onClick={handleLocate}
          className="border-b border-gray-600 bg-gray-900 px-5 py-3 text-white hover:bg-gray-700"
          title="Current location"
        >
          📍
        </button>

        <button
          onClick={handleLayers}
          className="border-b border-gray-600 bg-gray-900 px-5 py-3 text-white hover:bg-gray-700"
          title="Map layers"
        >
          🗺️
        </button>

        <button
          onClick={handleInfo}
          className="border-b border-gray-600 bg-gray-900 px-5 py-3 text-white hover:bg-gray-700"
          title="Information"
        >
          ℹ️
        </button>

        <button
          onClick={handleHelp}
          className="bg-gray-900 px-5 py-3 text-white hover:bg-gray-700"
          title="Help"
        >
          ?
        </button>
      </div>

      {showLayers && (
        <div className="absolute right-20 top-36 z-20 w-56 rounded-lg bg-white p-4 shadow-lg">
          <h2 className="font-bold text-gray-800">Map Layers</h2>

          <div className="mt-3 space-y-2 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked />
              Scenic routes
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked />
              Greenery areas
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" />
              Historical landmarks
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" />
              Water and lakes
            </label>
          </div>
        </div>
      )}

      {showInfo && (
        <div className="absolute right-20 top-72 z-20 w-64 rounded-lg bg-white p-4 shadow-lg">
          <h2 className="font-bold text-gray-800">Map Information</h2>

          <p className="mt-2 text-sm text-gray-600">
            This is a frontend placeholder. The real route, map tiles, and
            scenic score will come from the backend and map service later.
          </p>
        </div>
      )}

      <div className="absolute bottom-6 left-4 z-20 rounded bg-white/95 px-4 py-3 text-sm text-gray-800 shadow-lg">
        <div className="font-semibold">Scale</div>

        <div className="mt-2 flex items-end gap-2">
          <div
            className="border-b-4 border-l-2 border-r-2 border-black"
            style={{ width: `${scale.width}px`, height: "16px" }}
          ></div>
          <span>{scale.metric}</span>
        </div>

        <div className="mt-2 flex items-end gap-2">
          <div
            className="border-b-4 border-l-2 border-r-2 border-black"
            style={{ width: `${scale.width * 0.8}px`, height: "16px" }}
          ></div>
          <span>{scale.imperial}</span>
        </div>
      </div>

      <div className="absolute bottom-4 right-4 z-20 rounded bg-gray-900/80 px-4 py-2 text-xs text-white">
        Zoom: {zoom} | Scale: {scale.metric}
      </div>
    </div>
  );
}

function getScaleFromZoom(zoom) {
  const scales = {
    10: { metric: "5 km", imperial: "3 mi", width: 150 },
    11: { metric: "2 km", imperial: "1 mi", width: 140 },
    12: { metric: "1 km", imperial: "3000 ft", width: 130 },
    13: { metric: "500 m", imperial: "1500 ft", width: 120 },
    14: { metric: "250 m", imperial: "800 ft", width: 110 },
    15: { metric: "100 m", imperial: "300 ft", width: 100 },
    16: { metric: "50 m", imperial: "150 ft", width: 90 },
    17: { metric: "25 m", imperial: "75 ft", width: 80 },
    18: { metric: "10 m", imperial: "30 ft", width: 70 }
  };

  return scales[zoom];
}

export default Home;
