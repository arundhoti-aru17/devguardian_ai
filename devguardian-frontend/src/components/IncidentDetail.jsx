import React, { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  GitBranch,
  Plus,
  X,
  Check,
  Clock,
  AlertCircle,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";

import { fetchIncident, fetchIncidentMemory } from "./api/incidents";

const FILTERS = [
  "All",
  "Dependency",
  "Indentation",
  "Config",
  "Open only",
];

export default function IncidentDetail({
  selectedId,
  setSelectedId,
  setView,
  fetchIncidentStats,
  fetchIncidents,
}) {
  const [stats, setStats] = useState({
    total_incidents: 0,
    resolved_incidents: 0,
    open_prs: 0,
    accepted_incidents: 0,
    rejected_incidents: 0,
    human_review_incidents: 0,
    success_rate: 0,
  });

  const [incidents, setIncidents] = useState([]);
  const [activeFilter, setActiveFilter] = useState("All");

  useEffect(() => {
    async function loadStats() {
      try {
        const statsData = await fetchIncidentStats();
        if (statsData.success) {
          setStats(statsData.stats);
        }
      } catch (error) {
        console.error("Failed to load stats:", error);
      }
    }
    loadStats();
  }, [fetchIncidentStats]);

  useEffect(() => {
    async function loadIncidents() {
      try {
        const incidentsData = await fetchIncidents();
        if (incidentsData.success) {
          setIncidents(incidentsData.incidents);
        }
      } catch (error) {
        console.error("Failed to load incidents:", error);
      }
    }
    loadIncidents();
  }, [fetchIncidents]);

  const incident = selectedId ? incidents.find((i) => i.id === selectedId) : null;

  const goHome = () => {
    setView("home");
    setSelectedId(null);
  };

  const openIncident = (id) => {
    setSelectedId(id);
    setView("detail");
  };

  const formatIncidentDate = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString();
  };

  const formatIncidentDateTime = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  };

  if (!incident) {
    return (
      <div>
        <div className="panel">
          <div style={{ textAlign: "center", color: "var(--text-dim)", padding: "30px" }}>
            Select an incident from the list to view details
          </div>
        </div>
      </div>
    );
  }

  const incidentMemory = incident.memory
    ? incident.memory
    : null;

  return (
    <div>
      <button
        className="back-btn"
        onClick={goHome}
      >
        <ArrowLeft size={13} /> back to incidents
      </button>

      <div className="stat-rail">
        <div
          className="stat-card"
          style={{ "--stat-color": "var(--accent)" }}
        >
          <div className="stat-label">Total Incidents</div>
          <div className="stat-value">{stats.total_incidents}</div>
          <div className="stat-delta since project start">since project start</div>
        </div>
        <div
          className="stat-card"
          style={{ "--stat-color": "var(--ok)" }}
        >
          <div className="stat-label">Resolved</div>
          <div className="stat-value">{stats.resolved_incidents}</div>
          <div className="stat-delta up from database">from database</div>
        </div>
        <div
          className="stat-card"
          style={{ "--stat-color": "var(--warn)" }}
        >
          <div className="stat-label">Open PRs</div>
          <div className="stat-value">{stats.open_prs}</div>
          <div className="stat-delta">awaiting review</div>
        </div>
        <div
          className="stat-card"
          style={{ "--stat-color": "var(--accent)" }}
        >
          <div className="stat-label">Success Rate</div>
          <div className="stat-value">{stats.success_rate}%</div>
          <div className="stat-delta up fixes accepted on merge">fixes accepted on merge</div>
        </div>
      </div>

      <div className="section-head">
        <div className="section-title">Incident #{incident.id}</div>
        <div className="section-note">click a row to open the trace</div>
      </div>

      <div className="filters">
        {FILTERS.map((f) => (
          <button
            key={f}
            className={`chip ${
              activeFilter === f ? "active" : ""
            }`}
            onClick={() => setActiveFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="detail-grid">
        <div>
          <div className="panel">
            <div className="detail-header">

              <div>
                <div className="detail-eyebrow">
                  INCIDENT #{incident.id}
                </div>

                <div className="detail-title">
                  {incident.failure_type || "Unknown failure"}
                </div>

                <div className="detail-sub">
                  {incident.root_cause || "No root cause information available."}
                </div>
              </div>

            </div>

            <div style={{ marginTop: 28 }}>
              <div className="confidence-label">Outcome</div>

              <div
                className="confidence-value"
                style={{ textTransform: "lowercase", marginTop: 8 }}
              >
                {incident.outcome || "pending"}
              </div>

              <div className="confidence-track">

                <div
                  className="confidence-fill"
                  style={{
                    width:
                      incident.outcome === "accepted"
                        ? "100%"
                      : incident.outcome === "human_review"
                        ? "60%"
                      : "30%",
                  }}
                />
              </div>
            </div>
          </div>

          {/* TRACE */}
          <div className="trace-rail">

            <div
              className="trace-node"
              style={{ animationDelay: "0.15s" }}
            >

              <div className="trace-dot">
                <Check
                  size={11}
                  color="#5FD888"
                  strokeWidth={2.6}
                />
              </div>

              <div className="trace-node-title">
                Incident Detected
              </div>

              <div className="trace-node-detail">
                {incident.workflow || "CI workflow"} reported a{" "}
                {incident.failure_type || "workflow failure"}.
              </div>

              <div className="trace-node-time">
                {formatIncidentDateTime(incident.created_at)}
              </div>
            </div>

            <div
              className="trace-node"
              style={{ animationDelay: "0.25s" }}
            >

              <div className="trace-dot">
                <Check
                  size={11}
                  color="#5FD888"
                  strokeWidth={2.6}
                />
              </div>

              <div className="trace-node-title">
                Root Cause
              </div>

              <div className="trace-node-detail">
                {incident.root_cause || "Root cause analysis is not available."}
              </div>

              <div className="trace-node-time">
                diagnosed
              </div>
            </div>

            <div
              className="trace-node"
              style={{ animationDelay: "0.35s" }}
            >

              <div className="trace-dot">
                <Check
                  size={11}
                  color="#5FD888"
                  strokeWidth={2.6}
                />
              </div>

              <div className="trace-node-title">
                Remediation
              </div>

              <div className="trace-node-detail">
                {incident.fix_description || "No remediation description available."}
              </div>

              <div className="trace-node-time">
                {incident.outcome || "pending"}
              </div>
            </div>
          </div>
        </div>

        <div>
          {/* INCIDENT MEMORY */}
          <div className="panel">
            <div className="side-label">Incident Memory</div>

            {incident.memory ? (
              <div className="memory-card">

                <div className="memory-head">
                  <Clock size={13} /> similar incident matched
                </div>

                <div className="memory-title">
                  Incident #
                  {
                    incident.memory.incident_id
                  }{" "}
                  —{" "}
                  {
                    incident.memory.failure_type
                  }
                </div>

                <div className="memory-row">
                  Previous root cause:
                  {" "}
                  <b>
                    {
                      incident.memory.root_cause
                    }
                  </b>
                </div>

                <div className="memory-row">
                  Previous fix:
                  {" "}
                  <b>
                    {
                      incident.memory.fix_description
                    }
                  </b>
                </div>

                <div className="memory-row">
                  Outcome:
                  {" "}
                  <b
                    style={{ color: "var(--ok)" }}
                  >
                    {
                      incident.memory.outcome ||
                      "Unknown"
                    }
                  </b>
                </div>
              </div>
            ) : (
              <div className="no-match">

                <AlertCircle size={15} />

                <span>
                  No similar previous incidents found.
                  DevGuardian ran full diagnosis and generated a new remediation from scratch.
                </span>
              </div>
            )}
          </div>

          {/* PULL REQUEST */}
          <div className="panel">
            <div className="side-label">Pull Request</div>

            <div className="kv">

              <div className="kv-label">Number</div>

              <div className="kv-value">
                {incident.pr_number ? `#${incident.pr_number}` : "—"}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Status</div>

              <div
                className="kv-value"
                style={{ color: statusColor(incident.pr_status) }}
              >
                {incident.pr_status || "—"}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Target file</div>

              <div className="kv-value">
                {extractTargetFile(incident.fix_description)}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Branch</div>

              <div className="kv-value">
                {incident.branch || "—"}
              </div>

            </div>

            {incident.pr_number &&
            incident.repository && (
              <a
                className="pr-link"
                href={`https://github.com/${incident.repository}/pull/${incident.pr_number}`}
                target="_blank"
                rel="noreferrer"
              >

                <span
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 7,
                  }}
                >
                  View on GitHub
                </span>

                <ChevronRight
                  size={13}
                />

              </a>
            )}
          </div>

          {/* INCIDENT INFORMATION */}
          <div className="panel">
            <div className="side-label">Incident</div>

            <div className="kv">
              <div className="kv-label">Repository</div>

              <div className="kv-value">
                {incident.repository || "—"}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Workflow</div>

              <div className="kv-value">
                {incident.workflow || "—"}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Created</div>

              <div className="kv-value">
                {formatIncidentDateTime(incident.created_at)}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Workflow Run</div>

              <div className="kv-value">
                {incident.workflow_run_id || "—"}
              </div>

            </div>

            <div className="kv">
              <div className="kv-label">Feedback</div>

              <div className="kv-value">
                {incident.feedback || "—"}
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}