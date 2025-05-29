import React from "react";
import "./LoadingGradientBar.css";

export function LoadingGradientBar() {
  return (
    <div className="w-1/3 max-w-full h-2 rounded-full overflow-hidden bg-gray-200">
      <div className="loading-gradient-bar h-full w-full animate-gradient-x" />
    </div>
  );
}
