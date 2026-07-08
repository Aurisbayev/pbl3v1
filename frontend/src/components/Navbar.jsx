import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="flex h-16 items-center justify-between bg-gray-900 px-4 text-white shadow-md">
      <div className="flex items-center gap-6">
        <div className="text-xl font-bold">
          Scenic GPS
        </div>

        <div className="hidden gap-4 md:flex">
          <Link to="/" className="hover:text-green-400">
            Home
          </Link>

          <Link to="/route-selection" className="hover:text-green-400">
            Route Selection
          </Link>

          <Link to="/route-preview" className="hover:text-green-400">
            Route Preview
          </Link>

          <Link to="/navigation" className="hover:text-green-400">
            Navigation
          </Link>

          <Link to="/about" className="hover:text-green-400">
            About
          </Link>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="rounded border border-gray-500 px-3 py-1 hover:bg-gray-800">
          Log In
        </button>

        <button className="rounded border border-gray-500 px-3 py-1 hover:bg-gray-800">
          Sign Up
        </button>
      </div>
    </nav>
  );
}

export default Navbar;