import React from "react";
import { fetchIncidentStats, fetchIncidents, fetchIncident, fetchIncidentMemory } from "./api/incidents";
import { ShieldCheck, GitBranch, Plus, X, Check, Clock, AlertCircle, ChevronRight, ArrowLeft } from "lucide-react";

const FILTERS = [
  "All",
  "Dependency",
  "Indentation",
  "Config",
  "Open only",
];

const STATUS_BADGE_CLASSES = {
  open: "badge open",
  pending: "badge open",
  merged: "badge merged",
  blocked: "badge failed",
  rejected: "badge failed",
  human_review: "badge progress",
  accepted: "badge merged",
  "Inconclusive": "badge failed",
};

const OUTCOME_LABELS = {
  accepted: "Accepted",
  rejected: "Rejected",
  human_review: "Human review",
  merged: "Accepted",
  open: "Pending review",
  blocked: "Inconclusive",
};

const BADGE_CLASSES = {
  merged: "badge merged",
  open: "badge open",
  failed: "badge failed",
  progress: "badge progress",
};

function outcomeBadgeClass(value) {
  if (value === "accepted") return "merged";
  if (value === "rejected") return "failed";
  if (value === "human_review") return "progress";
  return "open";
}

function badgeClass(status) {
  if (status === "merged") return "merged";
  if (status === "open" || status === "pending") return "open";
  if (status === "blocked") return "failed";
  return "progress";
}

function outcomeLabel(status) {
  if (status === "accepted") return "Accepted";
  if (status === "rejected") return "Rejected";
  if (status === "human_review") return "Human review";
  if (status === "merged") return "Accepted";
  if (status === "open") return "Pending review";
  if (status === "blocked") return "Inconclusive";
  return status || "Unknown";
}

function extractTargetFile(description) {
  if (!description) return "—";
  const match = description.match(
    /(?:^|\s)([A-Za-z0-9_./-]+\.(?:py|txt|yml|yaml|json|toml|js|ts|jsx|tsx|java|go|rs|md))(?:\s|$|[.,])/i
  );
  return match ? match[1] : "—";
}

function statusColor(status) {
  if (status === "merged") return "var(--ok)";
  if (status === "blocked") return "var(--bad)";
  return "var(--warn)";
}

export default function IncidentTable({ onIncidentSelect, activeFilter = "All", incidents = [], incidentsLoading = true, incidentsError = "" }) {
  const filteredIncidents = incidents.filter((inc) => {
    if (activeFilter === "All") return true;
    if (activeFilter === "Open only") return inc.pr_status === "open";
    if (activeFilter === "Dependency") return (inc.failure_type || "").toLowerCase().includes("depend");
    if (activeFilter === "Indentation") return (inc.failure_type || "").toLowerCase().includes("indent");
    if (activeFilter === "Config") return inc.failure_type === "Missing Environment Variable";
    return true;
  });

  return (
    <div className="table-wrap">
      <div className="t-row head">
        <div>ID</div>
        <div>Failure</div>
        <div>PR</div>
        <div>Status</div>
        <div>Outcome</div>
        <div>When</div>
      </div>

      {incidentsLoading ? (
        <div style={{ padding: "24px", textAlign: "center", color: "var(--text-dim)" }}>
          Loading incidents...
        </div>
      ) : incidentsError ? (
        <div style={{ padding: "24px", textAlign: "center", color: "var(--bad)" }}>
          {incidentsError}
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div style={{ padding: "24px", textAlign: "center", color: "var(--text-dim)" }}>
          No incidents found.
        </div>
      ) : filteredIncidents.map((inc) => (
        <div
          className="t-row bodyrow"
          key={inc.id}
          onClick={() => onIncidentSelect(inc.id)}
        >

          <div className="t-id">{`#${inc.id}`}</div>

          <div className="t-main">
            <div className="t-failtype">{inc.failure_type || "Unknown failure"}</div>
            <div className="t-repo">
              {inc.repository || "—"}{" "}
              ·{" "}
              {inc.branch || inc.workflow || "—"}
            </div>
          </div>

          <div className="t-pr">
            {inc.pr_number ? `PR #${inc.pr_number}` : "—"}
          </div>

          <div>
            <span className={`badge ${outcomeBadgeClass(inc.pr_status || inc.status)}`}>
              {inc.pr_status || inc.status || "—"}
            </span>
          </div>

          <div>
            <span className={`badge ${outcomeLabel(inc.feedback || inc.outcome)}`}>
              {outcomeLabel(inc.feedback || inc.outcome)}
            </span>
          </div>

          <div className="t-time">{inc.created_at ? new Date(inc.created_at).toLocaleDateString() : "—"}</div>
        </div>
      ))}
    </div>
  );
}