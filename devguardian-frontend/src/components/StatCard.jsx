import React from "react";

const StatCard = ({ label, value, delta, deltaColor, style }) => {
  return (
    <div
      className="stat-card"
      style={{
        "--stat-color": style?.["--stat-color"],
        ...style,
      }}
    >
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {delta && (
        <div className={`stat-delta ${deltaColor ? "up" : ""}`}>
          {delta}
        </div>
      )}
    </div>
  );
};

export default StatCard;