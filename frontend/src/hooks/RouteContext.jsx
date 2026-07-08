import React, { createContext, useContext, useState } from "react";

const RouteContext = createContext(null);

export function RouteProvider({ children }) {
  const [currentRoute, setCurrentRoute] = useState(null);
  const [navigationSession, setNavigationSession] = useState(null);

  return (
    <RouteContext.Provider
      value={{
        currentRoute,
        setCurrentRoute,
        navigationSession,
        setNavigationSession,
      }}
    >
      {children}
    </RouteContext.Provider>
  );
}

export function useRouteContext() {
  const context = useContext(RouteContext);

  if (!context) {
    throw new Error("useRouteContext must be used inside RouteProvider");
  }

  return context;
}