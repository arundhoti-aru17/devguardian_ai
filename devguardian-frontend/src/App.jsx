import { useState, useRef, useEffect } from "react";

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

import {
  fetchIncidentStats,
  fetchIncidents,
  fetchIncident,
  fetchIncidentMemory,
} from "./api/incidents";

const FILTERS = [
  "All",
  "Dependency",
  "Indentation",
  "Config",
  "Open only",
];

/* ---------------------------------------------------------
   STYLE SHEET
--------------------------------------------------------- */

const CSS = `
:root{
  --bg:#0A0D13;
  --surface:#11151F;
  --surface-2:#161B27;
  --border:#232838;
  --border-soft:#1B202E;
  --text:#E7EAF2;
  --text-dim:#8890A4;
  --text-faint:#525A6E;
  --accent:#4FD1C5;
  --accent-dim:#2C7A72;
  --ok:#5FD888;
  --ok-dim:#1E3A2A;
  --warn:#F2B84B;
  --warn-dim:#3D3320;
  --bad:#F2665A;
  --bad-dim:#3A2222;
  --info:#5B8DEF;
  --info-dim:#1F2A44;
  --radius:10px;
  --mono:'JetBrains Mono', monospace;
  --display:'Space Grotesk', sans-serif;
  --body:'Inter', sans-serif;
}

.dg-root{
  background:
    radial-gradient(
      ellipse 900px 500px at 15% -10%,
      rgba(79,209,197,0.06),
      transparent 60%
    ),
    var(--bg);
  color:var(--text);
  font-family:var(--body);
  min-height:100vh;
  -webkit-font-smoothing:antialiased;
  border-radius:14px;
  overflow:hidden;
}

.dg-root *{
  box-sizing:border-box;
}

.dg-root button{
  font-family:inherit;
  cursor:pointer;
}

.dg-root :focus-visible{
  outline:2px solid var(--accent);
  outline-offset:2px;
}

.shell{
  max-width:1180px;
  margin:0 auto;
  padding:28px 24px 70px;
  position:relative;
}

.topbar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding-bottom:22px;
  margin-bottom:26px;
  border-bottom:1px solid var(--border-soft);
  flex-wrap:wrap;
  gap:14px;
}

.brand{
  display:flex;
  align-items:center;
  gap:11px;
}

.brand-mark{
  width:30px;
  height:30px;
  border-radius:8px;
  background:linear-gradient(
    155deg,
    var(--accent),
    var(--accent-dim)
  );
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:
    0 0 0 1px rgba(79,209,197,0.25),
    0 6px 16px -4px rgba(79,209,197,0.35);
  flex-shrink:0;
}

.brand-name{
  font-family:var(--display);
  font-weight:600;
  font-size:16.5px;
  letter-spacing:0.2px;
}

.brand-sub{
  font-family:var(--mono);
  font-size:10.5px;
  color:var(--text-faint);
  letter-spacing:0.06em;
  text-transform:uppercase;
  margin-top:1px;
}

.status-pill{
  display:flex;
  align-items:center;
  gap:7px;
  font-family:var(--mono);
  font-size:11.5px;
  color:var(--text-dim);
  border:1px solid var(--border);
  padding:6px 12px;
  border-radius:20px;
  background:var(--surface);
}

.live-dot{
  width:6px;
  height:6px;
  border-radius:50%;
  background:var(--ok);
  box-shadow:0 0 0 3px rgba(95,216,136,0.18);
  animation:pulse 2s ease-in-out infinite;
}

@keyframes pulse{
  0%,100%{opacity:1;}
  50%{opacity:0.4;}
}

@keyframes fadeIn{
  from{
    opacity:0;
    transform:translateY(4px);
  }
  to{
    opacity:1;
    transform:translateY(0);
  }
}

.btn-primary{
  display:flex;
  align-items:center;
  gap:7px;
  background:var(--accent);
  color:#06120F;
  border:none;
  border-radius:20px;
  font-family:var(--mono);
  font-size:11.5px;
  font-weight:600;
  letter-spacing:0.02em;
  padding:8px 14px 8px 12px;
  transition:filter .15s,transform .1s;
}

.btn-primary:hover{
  filter:brightness(1.08);
}

.btn-primary:active{
  transform:scale(0.97);
}

.stat-rail{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:14px;
  margin-bottom:28px;
}

.stat-card{
  background:var(--surface);
  border:1px solid var(--border-soft);
  border-radius:var(--radius);
  padding:18px 18px 16px;
  position:relative;
  overflow:hidden;
}

.stat-card::before{
  content:'';
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:2px;
  background:var(--stat-color,var(--accent));
  opacity:0.7;
}

.stat-label{
  font-family:var(--mono);
  font-size:10.5px;
  letter-spacing:0.08em;
  text-transform:uppercase;
  color:var(--text-faint);
}

.stat-value{
  font-family:var(--display);
  font-size:30px;
  font-weight:600;
  margin-top:8px;
  letter-spacing:-0.02em;
}

.stat-delta{
  font-size:12px;
  color:var(--text-dim);
  margin-top:5px;
}

.stat-delta.up{
  color:var(--ok);
}

.section-head{
  display:flex;
  align-items:baseline;
  justify-content:space-between;
  margin-bottom:12px;
}

.section-title{
  font-family:var(--display);
  font-size:15px;
  font-weight:600;
}

.section-note{
  font-family:var(--mono);
  font-size:11px;
  color:var(--text-faint);
}

.filters{
  display:flex;
  gap:8px;
  margin-bottom:14px;
  flex-wrap:wrap;
}

.chip{
  font-family:var(--mono);
  font-size:11.5px;
  color:var(--text-dim);
  background:var(--surface);
  border:1px solid var(--border-soft);
  border-radius:7px;
  padding:6px 11px;
  transition:all .15s;
}

.chip.active{
  color:var(--bg);
  background:var(--accent);
  border-color:var(--accent);
  font-weight:600;
}

.chip:hover:not(.active){
  border-color:var(--border);
  color:var(--text);
}

.table-wrap{
  background:var(--surface);
  border:1px solid var(--border-soft);
  border-radius:var(--radius);
  overflow:hidden;
}

.t-row{
  display:grid;
  grid-template-columns:
    56px
    1.6fr
    100px
    130px
    110px
    90px;
  align-items:center;
  padding:13px 18px;
  gap:10px;
  border-bottom:1px solid var(--border-soft);
  transition:background .12s;
}

.t-row:last-child{
  border-bottom:none;
}

.t-row.head{
  font-family:var(--mono);
  font-size:10px;
  text-transform:uppercase;
  letter-spacing:0.07em;
  color:var(--text-faint);
  padding:11px 18px;
}

.t-row.bodyrow{
  cursor:pointer;
}

.t-row.bodyrow:hover{
  background:var(--surface-2);
}

.t-id{
  font-family:var(--mono);
  color:var(--text-dim);
  font-size:12.5px;
}

.t-main{
  display:flex;
  flex-direction:column;
  gap:2px;
  min-width:0;
}

.t-failtype{
  font-size:13.5px;
  font-weight:500;
}

.t-repo{
  font-family:var(--mono);
  font-size:11px;
  color:var(--text-faint);
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}

.t-pr{
  font-family:var(--mono);
  font-size:12px;
  color:var(--text-dim);
}

.t-time{
  font-family:var(--mono);
  font-size:11px;
  color:var(--text-faint);
}

.badge{
  display:inline-flex;
  align-items:center;
  gap:5px;
  font-family:var(--mono);
  font-size:10.5px;
  font-weight:600;
  letter-spacing:0.03em;
  padding:4px 9px;
  border-radius:20px;
  width:fit-content;
  text-transform:uppercase;
}

.badge::before{
  content:'';
  width:5px;
  height:5px;
  border-radius:50%;
  background:currentColor;
}

.badge.merged{
  background:var(--ok-dim);
  color:var(--ok);
}

.badge.open{
  background:var(--warn-dim);
  color:var(--warn);
}

.badge.failed{
  background:var(--bad-dim);
  color:var(--bad);
}

.badge.progress{
  background:var(--info-dim);
  color:var(--info);
}

.back-btn{
  display:flex;
  align-items:center;
  gap:6px;
  background:none;
  border:none;
  color:var(--text-dim);
  font-family:var(--mono);
  font-size:12px;
  margin-bottom:18px;
  padding:4px 0;
}

.back-btn:hover{
  color:var(--accent);
}

.detail-grid{
  display:grid;
  grid-template-columns:1fr 340px;
  gap:18px;
  align-items:start;
}

.panel{
  background:var(--surface);
  border:1px solid var(--border-soft);
  border-radius:var(--radius);
  padding:20px;
}

.panel + .panel{
  margin-top:16px;
}

.detail-header{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:16px;
  flex-wrap:wrap;
}

.detail-eyebrow{
  font-family:var(--mono);
  font-size:11px;
  color:var(--accent);
  letter-spacing:0.06em;
}

.detail-title{
  font-family:var(--display);
  font-size:22px;
  font-weight:600;
  margin-top:6px;
}

.detail-sub{
  font-size:13px;
  color:var(--text-dim);
  margin-top:8px;
  max-width:520px;
  line-height:1.5;
}

.confidence-wrap{
  min-width:150px;
}

.confidence-label{
  font-family:var(--mono);
  font-size:10.5px;
  color:var(--text-faint);
  text-transform:uppercase;
  letter-spacing:0.06em;
  text-align:right;
  margin-bottom:6px;
}

.confidence-value{
  font-family:var(--display);
  font-size:24px;
  font-weight:600;
  text-align:right;
}

.confidence-track{
  height:5px;
  background:var(--border-soft);
  border-radius:4px;
  margin-top:8px;
  overflow:hidden;
}

.confidence-fill{
  height:100%;
  background:linear-gradient(
    90deg,
    var(--accent-dim),
    var(--accent)
  );
  border-radius:4px;
  transition:width .6s ease;
}

.trace-rail{
  position:relative;
  padding-left:26px;
  margin-top:22px;
}

.trace-rail::before{
  content:'';
  position:absolute;
  left:9px;
  top:8px;
  bottom:8px;
  width:2px;
  background:var(--border);
}

.trace-rail::after{
  content:'';
  position:absolute;
  left:9px;
  top:8px;
  width:2px;
  height:100%;
  background:linear-gradient(
    var(--accent),
    var(--ok)
  );
  animation:railFill 1.4s cubic-bezier(.4,0,.2,1);
}

@keyframes railFill{
  from{height:0%;}
  to{height:100%;}
}

.trace-node{
  position:relative;
  padding-bottom:22px;
  opacity:0;
  animation:nodeIn .4s ease forwards;
}

.trace-node:last-child{
  padding-bottom:0;
}

.trace-dot{
  position:absolute;
  left:-26px;
  top:1px;
  width:20px;
  height:20px;
  border-radius:50%;
  background:var(--surface-2);
  border:2px solid var(--ok);
  display:flex;
  align-items:center;
  justify-content:center;
}

.trace-node-title{
  font-family:var(--mono);
  font-size:12.5px;
  font-weight:600;
  color:var(--text);
}

.trace-node-detail{
  font-size:12.5px;
  color:var(--text-dim);
  margin-top:3px;
  line-height:1.5;
  max-width:460px;
}

.trace-node-time{
  font-family:var(--mono);
  font-size:10.5px;
  color:var(--text-faint);
  margin-top:4px;
}

@keyframes nodeIn{
  from{
    opacity:0;
    transform:translateX(-4px);
  }
  to{
    opacity:1;
    transform:translateX(0);
  }
}

.side-label{
  font-family:var(--mono);
  font-size:10.5px;
  text-transform:uppercase;
  letter-spacing:0.07em;
  color:var(--text-faint);
  margin-bottom:12px;
}

.kv{
  display:flex;
  justify-content:space-between;
  gap:14px;
  padding:9px 0;
  border-bottom:1px solid var(--border-soft);
  font-size:12.5px;
}

.kv:last-child{
  border-bottom:none;
}

.kv-label{
  color:var(--text-dim);
}

.kv-value{
  font-family:var(--mono);
  font-weight:500;
  text-align:right;
  overflow-wrap:anywhere;
}

.memory-card{
  border:1px solid var(--accent-dim);
  background:rgba(79,209,197,0.05);
  border-radius:8px;
  padding:14px;
}

.memory-head{
  display:flex;
  align-items:center;
  gap:7px;
  font-family:var(--mono);
  font-size:11px;
  color:var(--accent);
  text-transform:uppercase;
  letter-spacing:0.05em;
  margin-bottom:10px;
}

.memory-title{
  font-size:13px;
  font-weight:600;
}

.memory-row{
  font-size:12px;
  color:var(--text-dim);
  margin-top:7px;
  line-height:1.5;
}

.memory-row b{
  color:var(--text);
  font-weight:500;
}

.pr-link{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-top:10px;
  padding:10px 12px;
  background:var(--surface-2);
  border-radius:7px;
  font-family:var(--mono);
  font-size:12px;
  text-decoration:none;
  color:var(--text);
}

.pr-link:hover svg{
  transform:translateX(2px);
  color:var(--accent);
}

.pr-link svg{
  transition:all .15s ease;
  color:var(--text-faint);
}

.no-match{
  display:flex;
  gap:10px;
  align-items:flex-start;
  font-size:12.5px;
  color:var(--text-dim);
  line-height:1.55;
}

.no-match svg{
  flex-shrink:0;
  margin-top:2px;
  color:var(--text-faint);
}

.repo-panel{
  position:absolute;
  top:70px;
  right:24px;
  width:340px;
  z-index:20;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius);
  box-shadow:
    0 20px 40px -12px rgba(0,0,0,0.6);
  padding:14px;
  animation:fadeIn .2s ease;
}

.repo-item{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:9px 4px;
  border-bottom:1px solid var(--border-soft);
}

.repo-item:last-child{
  border-bottom:none;
}

.repo-item-name{
  font-family:var(--mono);
  font-size:12px;
}

.repo-item-meta{
  font-size:10.5px;
  color:var(--text-faint);
  margin-top:2px;
}

.repo-remove{
  background:none;
  border:none;
  color:var(--text-faint);
  font-size:15px;
  line-height:1;
  padding:4px;
}

.repo-remove:hover{
  color:var(--bad);
}

.modal-overlay{
  position:fixed;
  inset:0;
  background:rgba(6,8,12,0.72);
  backdrop-filter:blur(3px);
  display:flex;
  align-items:center;
  justify-content:center;
  z-index:50;
  padding:20px;
  animation:fadeIn .2s ease;
}

.modal{
  width:100%;
  max-width:440px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:14px;
  padding:24px;
  box-shadow:
    0 30px 60px -12px rgba(0,0,0,0.7);
}

.modal-title-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
}

.modal-title{
  font-family:var(--display);
  font-size:17px;
  font-weight:600;
}

.modal-close{
  background:none;
  border:none;
  color:var(--text-faint);
}

.modal-close:hover{
  color:var(--text);
}

.modal-sub{
  font-size:12.5px;
  color:var(--text-dim);
  margin-top:6px;
  line-height:1.5;
}

.field-label{
  font-family:var(--mono);
  font-size:10.5px;
  text-transform:uppercase;
  letter-spacing:0.06em;
  color:var(--text-faint);
  margin:18px 0 7px;
  display:block;
}

.field-input-wrap{
  display:flex;
  align-items:center;
  gap:8px;
  background:var(--surface-2);
  border:1px solid var(--border);
  border-radius:8px;
  padding:10px 12px;
  transition:border-color .15s;
}

.field-input-wrap.focused{
  border-color:var(--accent);
}

.field-input-wrap svg{
  color:var(--text-faint);
  flex-shrink:0;
}

.field-input{
  background:none;
  border:none;
  outline:none;
  color:var(--text);
  font-family:var(--mono);
  font-size:12.5px;
  width:100%;
}

.field-input::placeholder{
  color:var(--text-faint);
}

.field-error{
  font-size:11.5px;
  color:var(--bad);
  margin-top:6px;
}

.modal-actions{
  display:flex;
  justify-content:flex-end;
  gap:10px;
  margin-top:22px;
}

.btn-ghost{
  background:none;
  border:1px solid var(--border);
  color:var(--text-dim);
  border-radius:8px;
  padding:9px 16px;
  font-size:12.5px;
}

.btn-ghost:hover{
  color:var(--text);
  border-color:var(--text-faint);
}

.btn-confirm{
  background:var(--accent);
  color:#06120F;
  border:none;
  border-radius:8px;
  padding:9px 18px;
  font-size:12.5px;
  font-weight:600;
}

.btn-confirm:hover{
  filter:brightness(1.08);
}

.toast{
  position:fixed;
  bottom:26px;
  left:50%;
  transform:
    translateX(-50%)
    translateY(20px);
  background:var(--surface);
  border:1px solid var(--ok);
  color:var(--text);
  font-family:var(--mono);
  font-size:12.5px;
  padding:11px 18px;
  border-radius:8px;
  display:flex;
  align-items:center;
  gap:8px;
  opacity:0;
  pointer-events:none;
  transition:all .25s ease;
  z-index:60;
  box-shadow:
    0 12px 24px -8px rgba(0,0,0,0.5);
}

.toast.show{
  opacity:1;
  transform:
    translateX(-50%)
    translateY(0);
  pointer-events:auto;
}

@media (max-width:860px){
  .detail-grid{
    grid-template-columns:1fr;
  }
}

@media (max-width:640px){
  .repo-panel{
    right:12px;
    left:12px;
    width:auto;
  }

  .stat-rail{
    grid-template-columns:1fr 1fr;
  }

  .t-row{
    grid-template-columns:1fr;
    row-gap:6px;
  }

  .t-row.head{
    display:none;
  }

  .t-id{
    order:-1;
  }
}
`;

/* ---------------------------------------------------------
   COMPONENT
--------------------------------------------------------- */

export default function DevGuardianDashboard() {
  const [view, setView] = useState("home");
  const [selectedId, setSelectedId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [activeFilter, setActiveFilter] = useState("All");

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
  const [incidentsLoading, setIncidentsLoading] = useState(true);
  const [incidentsError, setIncidentsError] = useState("");

  const [repoPanelOpen, setRepoPanelOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const [urlValue, setUrlValue] = useState("");
  const [branchValue, setBranchValue] = useState("");

  const [urlFocused, setUrlFocused] = useState(false);
  const [branchFocused, setBranchFocused] = useState(false);

  const [urlError, setUrlError] = useState("");
  const [toast, setToast] = useState({
    show: false,
    msg: "",
  });

  const toastTimer = useRef(null);
  const panelRef = useRef(null);
  const pillRef = useRef(null);

  const [watchedRepos, setWatchedRepos] = useState([
    {
      name: "org/devguardian-demo",
      branch: "main",
      added: "12d ago",
    },
    {
      name: "org/payments-service",
      branch: "main",
      added: "6d ago",
    },
    {
      name: "org/internal-tools",
      branch: "develop",
      added: "2d ago",
    },
  ]);

  /* ---------------------------------------------------------
     CLOSE REPOSITORY PANEL
  --------------------------------------------------------- */

  useEffect(() => {
    function onClick(e) {
      if (
        repoPanelOpen &&
        panelRef.current &&
        !panelRef.current.contains(e.target) &&
        pillRef.current &&
        !pillRef.current.contains(e.target)
      ) {
        setRepoPanelOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      onClick
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        onClick
      );
    };
  }, [repoPanelOpen]);

  /* ---------------------------------------------------------
     ESCAPE KEY
  --------------------------------------------------------- */

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") {
        setModalOpen(false);
      }
    }

    document.addEventListener(
      "keydown",
      onKey
    );

    return () => {
      document.removeEventListener(
        "keydown",
        onKey
      );
    };
  }, []);

  /* ---------------------------------------------------------
     LOAD DASHBOARD DATA
  --------------------------------------------------------- */

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const statsData =
          await fetchIncidentStats();

        if (statsData.success) {
          setStats(statsData.stats);
        }

        const incidentsData =
          await fetchIncidents();

        if (incidentsData.success) {
          setIncidents(
            incidentsData.incidents
          );

          console.log(
            "DevGuardian: loaded",
            incidentsData.incidents.length,
            "real incidents"
          );
        } else {
          setIncidentsError(
            "Failed to load incidents"
          );
        }
      } catch (error) {
        console.error(
          "Failed to load dashboard data:",
          error
        );

        setIncidentsError(
          "Unable to connect to DevGuardian API"
        );
      } finally {
        setIncidentsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  /* ---------------------------------------------------------
     LOAD SELECTED INCIDENT
  --------------------------------------------------------- */

  useEffect(() => {
    async function loadSelectedIncident() {
      if (!selectedId) {
        setSelectedIncident(null);
        return;
      }

      try {
        const incidentData =
          await fetchIncident(selectedId);

        if (!incidentData.success) {
          setSelectedIncident(null);
          return;
        }

        let memory = null;

        try {
          const memoryData =
            await fetchIncidentMemory(
              selectedId
            );

          if (memoryData.success) {
            memory = memoryData.memory;
          }
        } catch (memoryError) {
          console.warn(
            `Incident memory unavailable for ${selectedId}:`,
            memoryError
          );
        }

        setSelectedIncident({
          ...incidentData.incident,
          memory,
        });
      } catch (error) {
        console.error(
          `Failed to load incident ${selectedId}:`,
          error
        );

        setSelectedIncident(null);
      }
    }

    loadSelectedIncident();
  }, [selectedId]);

  /* ---------------------------------------------------------
     TOAST
  --------------------------------------------------------- */

  function showToast(msg) {
    setToast({
      show: true,
      msg,
    });

    clearTimeout(
      toastTimer.current
    );

    toastTimer.current = setTimeout(() => {
      setToast({
        show: false,
        msg: "",
      });
    }, 3200);
  }

  /* ---------------------------------------------------------
     INCIDENT NAVIGATION
  --------------------------------------------------------- */

  function openIncident(id) {
    setSelectedId(id);
    setView("detail");
  }

  function goHome() {
    setView("home");
    setSelectedId(null);
    setSelectedIncident(null);
  }

  /* ---------------------------------------------------------
     GITHUB REPOSITORY
  --------------------------------------------------------- */

  function parseGithubUrl(raw) {
    const trimmed = raw
      .trim()
      .replace(/\/+$/, "");

    const m = trimmed.match(
      /^(?:https?:\/\/)?(?:www\.)?github\.com\/([\w.-]+)\/([\w.-]+)$/i
    );

    return m
      ? `${m[1]}/${m[2]}`
      : null;
  }

  function openConnectModal() {
    setRepoPanelOpen(false);
    setUrlValue("");
    setBranchValue("");
    setUrlError("");
    setModalOpen(true);
  }

  function submitRepo() {
    const parsed =
      parseGithubUrl(urlValue);

    if (!parsed) {
      setUrlError(
        "Enter a valid GitHub repository URL, like https://github.com/org/repo"
      );
      return;
    }

    if (
      watchedRepos.some(
        (r) =>
          r.name.toLowerCase() ===
          parsed.toLowerCase()
      )
    ) {
      setUrlError(
        "This repository is already connected."
      );
      return;
    }

    setWatchedRepos((prev) => [
      {
        name: parsed,
        branch:
          branchValue.trim() ||
          "main",
        added: "just now",
      },
      ...prev,
    ]);

    setModalOpen(false);

    showToast(
      `Connected ${parsed} — DevGuardian will watch for failed runs.`
    );
  }

  function removeRepo(i) {
    const removed =
      watchedRepos[i];

    setWatchedRepos((prev) =>
      prev.filter(
        (_, idx) => idx !== i
      )
    );

    showToast(
      `Stopped watching ${removed.name}`
    );
  }

  /* ---------------------------------------------------------
     INCIDENT DATA
  --------------------------------------------------------- */

  const incident =
    selectedIncident;

  const filteredIncidents =
    incidents.filter((inc) => {
      if (
        activeFilter === "All"
      ) {
        return true;
      }

      if (
        activeFilter ===
        "Open only"
      ) {
        return (
          inc.pr_status ===
          "open"
        );
      }

      if (
        activeFilter ===
        "Dependency"
      ) {
        return (
          inc.failure_type ||
          ""
        )
          .toLowerCase()
          .includes("depend");
      }

      if (
        activeFilter ===
        "Indentation"
      ) {
        return (
          inc.failure_type ||
          ""
        )
          .toLowerCase()
          .includes("indent");
      }

      if (
        activeFilter ===
        "Config"
      ) {
        return (
          inc.failure_type === "Missing Environment Variable"
        );
      }

      return true;
    });

  return (
    <div className="dg-root">
      <style>{CSS}</style>

      <div className="shell">

        {/* =====================================================
            TOPBAR
        ===================================================== */}

        <div className="topbar">

          <div className="brand">

            <div className="brand-mark">
              <ShieldCheck
                size={16}
                color="#0A0D13"
                strokeWidth={2.4}
              />
            </div>

            <div>
              <div className="brand-name">
                DevGuardian
              </div>

              <div className="brand-sub">
                Incident Console
              </div>
            </div>

          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >

            <button
              ref={pillRef}
              className="status-pill"
              onClick={() =>
                setRepoPanelOpen(
                  (o) => !o
                )
              }
            >
              <span className="live-dot" />

              watching{" "}
              {watchedRepos.length}{" "}
              repositor
              {watchedRepos.length === 1
                ? "y"
                : "ies"}
            </button>

            <button
              className="btn-primary"
              onClick={
                openConnectModal
              }
            >
              <Plus
                size={13}
                strokeWidth={2.5}
              />

              Connect repository
            </button>

          </div>

          {repoPanelOpen && (
            <div
              className="repo-panel"
              ref={panelRef}
            >

              <div className="side-label">
                Watched repositories
              </div>

              {watchedRepos.length ===
              0 ? (
                <div
                  className="no-match"
                  style={{
                    padding:
                      "6px 4px",
                  }}
                >
                  No repositories
                  connected yet.
                </div>
              ) : (
                watchedRepos.map(
                  (r, i) => (
                    <div
                      className="repo-item"
                      key={
                        r.name + i
                      }
                    >

                      <div>
                        <div className="repo-item-name">
                          {r.name}
                        </div>

                        <div className="repo-item-meta">
                          watching{" "}
                          {r.branch} · added{" "}
                          {r.added}
                        </div>
                      </div>

                      <button
                        className="repo-remove"
                        onClick={() =>
                          removeRepo(i)
                        }
                        aria-label={`Stop watching ${r.name}`}
                      >
                        <X size={13} />
                      </button>

                    </div>
                  )
                )
              )}

            </div>
          )}

        </div>

        {/* =====================================================
            HOME VIEW
        ===================================================== */}

        {view === "home" && (
          <div
            style={{
              animation:
                "fadeIn .3s ease",
            }}
          >

            <div className="stat-rail">

              <div
                className="stat-card"
                style={{
                  "--stat-color":
                    "var(--accent)",
                }}
              >
                <div className="stat-label">
                  Total Incidents
                </div>

                <div className="stat-value">
                  {stats.total_incidents}
                </div>

                <div className="stat-delta">
                  since project start
                </div>
              </div>

              <div
                className="stat-card"
                style={{
                  "--stat-color":
                    "var(--ok)",
                }}
              >
                <div className="stat-label">
                  Resolved
                </div>

                <div className="stat-value">
                  {stats.resolved_incidents}
                </div>

                <div className="stat-delta up">
                  from database
                </div>
              </div>

              <div
                className="stat-card"
                style={{
                  "--stat-color":
                    "var(--warn)",
                }}
              >
                <div className="stat-label">
                  Open PRs
                </div>

                <div className="stat-value">
                  {stats.open_prs}
                </div>

                <div className="stat-delta">
                  awaiting review
                </div>
              </div>

              <div
                className="stat-card"
                style={{
                  "--stat-color":
                    "var(--accent)",
                }}
              >
                <div className="stat-label">
                  Success Rate
                </div>

                <div className="stat-value">
                  {stats.success_rate}%
                </div>

                <div className="stat-delta up">
                  fixes accepted on merge
                </div>
              </div>

            </div>

            <div className="section-head">

              <div className="section-title">
                Recent Incidents
              </div>

              <div className="section-note">
                click a row to open the trace
              </div>

            </div>

            <div className="filters">

              {FILTERS.map(
                (f) => (
                  <button
                    key={f}
                    className={`chip ${
                      activeFilter === f
                        ? "active"
                        : ""
                    }`}
                    onClick={() =>
                      setActiveFilter(f)
                    }
                  >
                    {f}
                  </button>
                )
              )}

            </div>

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
                <div
                  style={{
                    padding: "24px",
                    textAlign:
                      "center",
                    color:
                      "var(--text-dim)",
                  }}
                >
                  Loading incidents...
                </div>
              ) : incidentsError ? (
                <div
                  style={{
                    padding: "24px",
                    textAlign:
                      "center",
                    color:
                      "var(--bad)",
                  }}
                >
                  {incidentsError}
                </div>
              ) : filteredIncidents.length ===
                0 ? (
                <div
                  style={{
                    padding: "24px",
                    textAlign:
                      "center",
                    color:
                      "var(--text-dim)",
                  }}
                >
                  No incidents found.
                </div>
              ) : (
                filteredIncidents.map(
                  (inc) => (
                    <div
                      className="t-row bodyrow"
                      key={inc.id}
                      onClick={() =>
                        openIncident(
                          inc.id
                        )
                      }
                    >

                      <div className="t-id">
                        #{inc.id}
                      </div>

                      <div className="t-main">

                        <div className="t-failtype">
                          {inc.failure_type ||
                            "Unknown failure"}
                        </div>

                        <div className="t-repo">
                          {inc.repository ||
                            "—"}{" "}
                          ·{" "}
                          {inc.branch ||
                            inc.workflow ||
                            "—"}
                        </div>

                      </div>

                      <div className="t-pr">
                        {inc.pr_number
                          ? `PR #${inc.pr_number}`
                          : "—"}
                      </div>

                      <div>
                        <span
                          className={`badge ${badgeClass(
                            inc.pr_status ||
                              inc.status
                          )}`}
                        >
                          {inc.pr_status ||
                            inc.status ||
                            "—"}
                        </span>
                      </div>

                      <div>
                        <span
                          className={`badge ${outcomeBadgeClass(
                            inc.feedback ||
                              inc.outcome
                          )}`}
                        >
                          {outcomeLabel(
                            inc.feedback ||
                              inc.outcome
                          )}
                        </span>
                      </div>

                      <div className="t-time">
                        {formatIncidentDate(
                          inc.created_at
                        )}
                      </div>

                    </div>
                  )
                )
              )}

            </div>

          </div>
        )}

        {/* =====================================================
            DETAIL VIEW
        ===================================================== */}

        {view === "detail" && (
          <div
            style={{
              animation:
                "fadeIn .3s ease",
            }}
          >

            <button
              className="back-btn"
              onClick={goHome}
            >
              <ArrowLeft size={13} />

              back to incidents
            </button>

            {!incident ? (
              <div className="panel">

                <div
                  style={{
                    textAlign:
                      "center",
                    color:
                      "var(--text-dim)",
                    padding: "30px",
                  }}
                >
                  Loading incident...
                </div>

              </div>
            ) : (
              <div className="detail-grid">

                {/* =================================================
                    LEFT COLUMN
                ================================================= */}

                <div>

                  <div className="panel">

                    <div className="detail-header">

                      <div>

                        <div className="detail-eyebrow">
                          INCIDENT #{incident.id}
                        </div>

                        <div className="detail-title">
                          {incident.failure_type ||
                            "Unknown failure"}
                        </div>

                        <div className="detail-sub">
                          {incident.root_cause ||
                            "No root cause information available."}
                        </div>

                      </div>

                    </div>

                    <div
                      style={{
                        marginTop: 28,
                      }}
                    >

                      <div className="confidence-label">
                        Outcome
                      </div>

                      <div
                        className="confidence-value"
                        style={{
                          textTransform:
                            "lowercase",
                          marginTop: 8,
                        }}
                      >
                        {incident.outcome ||
                          "pending"}
                      </div>

                      <div className="confidence-track">

                        <div
                          className="confidence-fill"
                          style={{
                            width:
                              incident.outcome ===
                              "accepted"
                                ? "100%"
                                : incident.outcome ===
                                  "human_review"
                                ? "60%"
                                : "30%",
                          }}
                        />

                      </div>

                    </div>

                    {/* TRACE */}

                    <div className="trace-rail">

                      <div
                        className="trace-node"
                        style={{
                          animationDelay:
                            "0.15s",
                        }}
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
                          {incident.workflow ||
                            "CI workflow"}{" "}
                          reported a{" "}
                          {incident.failure_type ||
                            "workflow failure"}.
                        </div>

                        <div className="trace-node-time">
                          {formatIncidentDateTime(
                            incident.created_at
                          )}
                        </div>

                      </div>

                      <div
                        className="trace-node"
                        style={{
                          animationDelay:
                            "0.25s",
                        }}
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
                          {incident.root_cause ||
                            "Root cause analysis is not available."}
                        </div>

                        <div className="trace-node-time">
                          diagnosed
                        </div>

                      </div>

                      <div
                        className="trace-node"
                        style={{
                          animationDelay:
                            "0.35s",
                        }}
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
                          {incident.fix_description ||
                            "No remediation description available."}
                        </div>

                        <div className="trace-node-time">
                          {incident.outcome ||
                            "pending"}
                        </div>

                      </div>

                    </div>

                  </div>

                </div>

                {/* =================================================
                    RIGHT COLUMN
                ================================================= */}

                <div>

                  {/* INCIDENT MEMORY */}

                  <div className="panel">

                    <div className="side-label">
                      Incident Memory
                    </div>

                    {incident.memory ? (
                      <div className="memory-card">

                        <div className="memory-head">
                          <Clock size={13} />

                          similar incident matched
                        </div>

                        <div className="memory-title">
                          Incident #
                          {
                            incident
                              .memory
                              .incident_id
                          }{" "}
                          —{" "}
                          {
                            incident
                              .memory
                              .failure_type
                          }
                        </div>

                        <div className="memory-row">
                          Previous root cause:
                          {" "}
                          <b>
                            {
                              incident
                                .memory
                                .root_cause
                            }
                          </b>
                        </div>

                        <div className="memory-row">
                          Previous fix:
                          {" "}
                          <b>
                            {
                              incident
                                .memory
                                .fix_description
                            }
                          </b>
                        </div>

                        <div className="memory-row">
                          Outcome:
                          {" "}
                          <b
                            style={{
                              color:
                                "var(--ok)",
                            }}
                          >
                            {
                              incident
                                .memory
                                .outcome ||
                              "Unknown"
                            }
                          </b>
                        </div>

                      </div>
                    ) : (
                      <div className="no-match">

                        <AlertCircle
                          size={15}
                        />

                        <span>
                          No similar previous
                          incidents found.
                          DevGuardian ran full
                          diagnosis and generated
                          a new remediation from
                          scratch.
                        </span>

                      </div>
                    )}

                  </div>

                  {/* PULL REQUEST */}

                  <div className="panel">

                    <div className="side-label">
                      Pull Request
                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Number
                      </div>

                      <div className="kv-value">
                        {incident.pr_number
                          ? `#${incident.pr_number}`
                          : "—"}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Status
                      </div>

                      <div
                        className="kv-value"
                        style={{
                          color:
                            statusColor(
                              incident.pr_status
                            ),
                        }}
                      >
                        {incident.pr_status ||
                          "—"}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Target file
                      </div>

                      <div className="kv-value">
                        {extractTargetFile(
                          incident.fix_description
                        )}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Branch
                      </div>

                      <div className="kv-value">
                        {incident.branch ||
                          "—"}
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
                              display:
                                "flex",
                              alignItems:
                                "center",
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

                    <div className="side-label">
                      Incident
                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Repository
                      </div>

                      <div className="kv-value">
                        {incident.repository ||
                          "—"}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Workflow
                      </div>

                      <div className="kv-value">
                        {incident.workflow ||
                          "—"}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Created
                      </div>

                      <div className="kv-value">
                        {formatIncidentDateTime(
                          incident.created_at
                        )}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Workflow Run
                      </div>

                      <div className="kv-value">
                        {incident.workflow_run_id ||
                          "—"}
                      </div>

                    </div>

                    <div className="kv">

                      <div className="kv-label">
                        Feedback
                      </div>

                      <div className="kv-value">
                        {incident.feedback ||
                          "—"}
                      </div>

                    </div>

                  </div>

                </div>

              </div>
            )}

          </div>
        )}

        {/* =====================================================
            CONNECT REPOSITORY MODAL
        ===================================================== */}

        {modalOpen && (
          <div
            className="modal-overlay"
            onClick={(e) => {
              if (
                e.target ===
                e.currentTarget
              ) {
                setModalOpen(false);
              }
            }}
          >

            <div className="modal">

              <div className="modal-title-row">

                <div className="modal-title">
                  Connect a repository
                </div>

                <button
                  className="modal-close"
                  onClick={() =>
                    setModalOpen(false)
                  }
                >
                  <X size={16} />
                </button>

              </div>

              <div className="modal-sub">
                DevGuardian will listen for failed
                GitHub Actions runs on this
                repository and open remediation
                PRs automatically.
              </div>

              <label className="field-label">
                Repository URL
              </label>

              <div
                className={`field-input-wrap ${
                  urlFocused
                    ? "focused"
                    : ""
                }`}
              >

                <GitBranch size={15} />

                <input
                  className="field-input"
                  placeholder="https://github.com/org/repository"
                  value={urlValue}
                  onChange={(e) => {
                    setUrlValue(
                      e.target.value
                    );

                    if (urlError) {
                      setUrlError("");
                    }
                  }}
                  onFocus={() =>
                    setUrlFocused(true)
                  }
                  onBlur={() =>
                    setUrlFocused(false)
                  }
                  onKeyDown={(e) => {
                    if (
                      e.key ===
                      "Enter"
                    ) {
                      submitRepo();
                    }
                  }}
                  autoFocus
                />

              </div>

              {urlError && (
                <div className="field-error">
                  {urlError}
                </div>
              )}

              <label className="field-label">
                Branch to watch
              </label>

              <div
                className={`field-input-wrap ${
                  branchFocused
                    ? "focused"
                    : ""
                }`}
              >

                <GitBranch size={15} />

                <input
                  className="field-input"
                  placeholder="main"
                  value={branchValue}
                  onChange={(e) =>
                    setBranchValue(
                      e.target.value
                    )
                  }
                  onFocus={() =>
                    setBranchFocused(true)
                  }
                  onBlur={() =>
                    setBranchFocused(false)
                  }
                  onKeyDown={(e) => {
                    if (
                      e.key ===
                      "Enter"
                    ) {
                      submitRepo();
                    }
                  }}
                />

              </div>

              <div className="modal-actions">

                <button
                  className="btn-ghost"
                  onClick={() =>
                    setModalOpen(false)
                  }
                >
                  Cancel
                </button>

                <button
                  className="btn-confirm"
                  onClick={
                    submitRepo
                  }
                >
                  Connect repository
                </button>

              </div>

            </div>

          </div>
        )}

        {/* =====================================================
            TOAST
        ===================================================== */}

        <div
          className={`toast ${
            toast.show
              ? "show"
              : ""
          }`}
        >
          <Check
            size={14}
            color="#5FD888"
            strokeWidth={2.6}
          />

          {toast.msg}
        </div>

      </div>
    </div>
  );
}

/* =========================================================
   HELPERS
========================================================= */

function formatIncidentDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString();
}

function formatIncidentDateTime(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function outcomeBadgeClass(value) {
  if (value === "accepted") {
    return "merged";
  }

  if (value === "rejected") {
    return "failed";
  }

  if (value === "human_review") {
    return "progress";
  }

  return "open";
}

function badgeClass(status) {
  if (status === "merged") {
    return "merged";
  }

  if (
    status === "open" ||
    status === "pending"
  ) {
    return "open";
  }

  if (status === "blocked") {
    return "failed";
  }

  return "progress";
}

function outcomeLabel(status) {
  if (status === "accepted") {
    return "Accepted";
  }

  if (status === "rejected") {
    return "Rejected";
  }

  if (status === "human_review") {
    return "Human review";
  }

  if (status === "merged") {
    return "Accepted";
  }

  if (status === "open") {
    return "Pending review";
  }

  if (status === "blocked") {
    return "Inconclusive";
  }

  return status || "Unknown";
}

function extractTargetFile(description) {
  if (!description) {
    return "—";
  }

  const match = description.match(
    /(?:^|\s)([A-Za-z0-9_./-]+\.(?:py|txt|yml|yaml|json|toml|js|ts|jsx|tsx|java|go|rs|md))(?:\s|$|[.,])/i
  );

  return match
    ? match[1]
    : "—";
}

function statusColor(status) {
  if (status === "merged") {
    return "var(--ok)";
  }

  if (status === "blocked") {
    return "var(--bad)";
  }

  return "var(--warn)";
}