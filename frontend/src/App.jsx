import React from "react";
import { Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import RouteSelection from "./pages/RouteSelection";
import RoutePreview from "./pages/RoutePreview";
import Navigation from "./pages/Navigation";
import About from "./pages/About";

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/route-selection" element={<RouteSelection />} />
        <Route path="/route-preview" element={<RoutePreview />} />
        <Route path="/navigation" element={<Navigation />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </div>
  );
}

export default App;
