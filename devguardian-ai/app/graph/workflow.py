import time

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from app.graph.state import DevGuardianState

from app.agents.ci_agent import CIAgent
from app.agents.docker_agent import DockerAgent
from app.agents.kubernetes_agent import KubernetesAgent
from app.agents.fix_agent import FixAgent

from app.services.fix_safety import FixSafetyChecker
from app.services.patch_validator import PatchValidator
from app.services.github_api import GitHubAPI
from app.services.github_remediation import GitHubRemediation
from app.services.incident_memory import IncidentMemory

from app.db.session import SessionLocal
from app.db.models import Incident

from app.core.config import settings


# =========================================================
# CREATE AGENTS / SERVICES
# =========================================================

ci_agent = CIAgent()
docker_agent = DockerAgent()
kubernetes_agent = KubernetesAgent()
fix_agent = FixAgent()

safety_checker = FixSafetyChecker()
patch_validator = PatchValidator()

# M6 — Incident Memory
incident_memory = IncidentMemory()


# =========================================================
# RETRY HELPER
# =========================================================

def run_with_retries(
    operation,
    operation_name: str,
    max_attempts: int = 3,
):
    """
    Execute an operation with retry support.

    Retry schedule:

        Attempt 1
             ↓ failure
        wait 1 second
             ↓
        Attempt 2
             ↓ failure
        wait 2 seconds
             ↓
        Attempt 3
             ↓
        success OR final failure
    """

    last_error = None

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"🔄 {operation_name} "
                f"(attempt {attempt}/{max_attempts})"
            )

            return operation()

        except Exception as exc:

            last_error = exc

            print(
                f"⚠️ {operation_name} failed: {exc}"
            )

            # -------------------------------------------------
            # Retry only if attempts remain
            # -------------------------------------------------

            if attempt < max_attempts:

                wait_time = 2 ** (attempt - 1)

                print(
                    f"⏳ Retrying {operation_name} "
                    f"in {wait_time} second(s)..."
                )

                time.sleep(wait_time)

    # ---------------------------------------------------------
    # All attempts failed
    # ---------------------------------------------------------

    print(
        f"❌ {operation_name} failed after "
        f"{max_attempts} attempts."
    )

    raise last_error


# =========================================================
# ROUTER NODE
# =========================================================

def router_node(state: DevGuardianState):
    """
    Decide which diagnosis agent should process the logs.
    """

    logs = state["logs"]
    logs_lower = logs.lower()

    # ---------------------------------------------------------
    # Kubernetes
    # ---------------------------------------------------------

    if (
        "imagepullbackoff" in logs_lower
        or "errimagepull" in logs_lower
        or "crashloopbackoff" in logs_lower
        or "kubernetes" in logs_lower
        or "kubectl" in logs_lower
        or "pod" in logs_lower
        or "deployment" in logs_lower
    ):

        print(
            "☸️ LangGraph -> Kubernetes Agent"
        )

        return {
            "route": "kubernetes",
        }

    # ---------------------------------------------------------
    # Docker
    # ---------------------------------------------------------

    if (
        "dockerfile" in logs_lower
        or "failed to solve" in logs_lower
        or "docker build" in logs_lower
    ):

        print(
            "📦 LangGraph -> Docker Agent"
        )

        return {
            "route": "docker",
        }

    # ---------------------------------------------------------
    # Default → CI
    # ---------------------------------------------------------

    print(
        "⚙️ LangGraph -> CI Agent"
    )

    return {
        "route": "ci",
    }


# =========================================================
# CI AGENT NODE
# =========================================================

def ci_agent_node(state: DevGuardianState):
    """
    Run the CI Agent with retry support.
    """

    diagnosis = run_with_retries(
        lambda: ci_agent.diagnose(
            state["logs"]
        ),
        "CI Agent",
    )

    return {
        "diagnosis": diagnosis,
    }


# =========================================================
# DOCKER AGENT NODE
# =========================================================

def docker_agent_node(state: DevGuardianState):
    """
    Run the Docker Agent with retry support.
    """

    diagnosis = run_with_retries(
        lambda: docker_agent.diagnose(
            state["logs"]
        ),
        "Docker Agent",
    )

    return {
        "diagnosis": diagnosis,
    }


# =========================================================
# KUBERNETES AGENT NODE
# =========================================================

def kubernetes_agent_node(state: DevGuardianState):
    """
    Run the Kubernetes Agent with retry support.
    """

    diagnosis = run_with_retries(
        lambda: kubernetes_agent.diagnose(
            state["logs"]
        ),
        "Kubernetes Agent",
    )

    return {
        "diagnosis": diagnosis,
    }


# =========================================================
# M6 — INCIDENT MEMORY NODE
# =========================================================

def incident_memory_node(state: DevGuardianState):
    """
    Search previous incidents that are semantically similar
    to the current diagnosis.

    The current diagnosis is represented as a temporary
    Incident object. It is NOT saved to the database here.

    IncidentMemory generates an embedding for the current
    diagnosis and searches PostgreSQL + pgvector for the
    closest previous incidents.
    """

    diagnosis = state.get(
        "diagnosis"
    )

    # ---------------------------------------------------------
    # No diagnosis available
    # ---------------------------------------------------------

    if diagnosis is None:

        print(
            "⚠️ Incident Memory skipped: "
            "no diagnosis available."
        )

        return {
            "memory_context": None,
        }

    db = SessionLocal()

    try:

        print(
            "\n🧠 LangGraph -> Incident Memory"
        )

        # -----------------------------------------------------
        # Create temporary representation of current incident
        # -----------------------------------------------------

        current_incident = Incident(
            repository=state.get(
                "repo_name",
                "Unknown",
            ),
            branch=state.get(
                "base_branch",
                "Unknown",
            ),
            workflow="Current Incident",
            status="diagnosed",
            failure_type=diagnosis.failure_type,
            root_cause=diagnosis.root_cause,
            fix_description=None,
            outcome=None,
        )

        # -----------------------------------------------------
        # Search previous incidents
        # -----------------------------------------------------

        similar_incidents = (
            incident_memory.find_similar_incidents(
                db=db,
                incident=current_incident,
                limit=5,
            )
        )

        # -----------------------------------------------------
        # No previous memory
        # -----------------------------------------------------

        if not similar_incidents:

            print(
                "🧠 No similar previous incidents found."
            )

            return {
                "memory_context": None,
            }

        # -----------------------------------------------------
        # Build memory context
        # -----------------------------------------------------

        memory_lines = [
            "Previous similar incidents:"
        ]

        for incident in similar_incidents:

            memory_lines.append(
                (
                    f"Incident #{incident.id}\n"
                    f"Failure type: "
                    f"{incident.failure_type or 'Unknown'}\n"
                    f"Root cause: "
                    f"{incident.root_cause or 'Unknown'}\n"
                    f"Fix: "
                    f"{incident.fix_description or 'Unknown'}\n"
                    f"Outcome: "
                    f"{incident.outcome or 'Unknown'}"
                )
            )

        memory_context = (
            "\n\n".join(memory_lines)
        )

        # -----------------------------------------------------
        # Print memory for debugging
        # -----------------------------------------------------

        print(
            "\n========== INCIDENT MEMORY ==========\n"
        )

        print(
            memory_context
        )

        print(
            "\n=====================================\n"
        )

        return {
            "memory_context": memory_context,
        }

    except Exception as exc:

        print(
            f"⚠️ Incident memory search failed: {exc}"
        )

        # -----------------------------------------------------
        # Memory failure should NOT break the whole graph.
        # -----------------------------------------------------

        return {
            "memory_context": None,
        }

    finally:

        db.close()


# =========================================================
# FIX AGENT NODE
# =========================================================

def fix_agent_node(state: DevGuardianState):
    """
    Generate a fix using the actual repository contents.

    M6 memory is passed into the Fix Agent.
    """

    diagnosis = state["diagnosis"]

    fix = run_with_retries(
        lambda: fix_agent.generate_fix(
            diagnosis=diagnosis,
            repo_path=state["repo_path"],
            logs=state["logs"],
            memory_context=state.get(
                "memory_context"
            ),
        ),
        "Fix Agent",
    )

    return {
        "fix": fix,
    }


# =========================================================
# PATCH VALIDATOR NODE
# =========================================================

def patch_validator_node(state: DevGuardianState):
    """
    Validate that the generated patch actually matches
    the current repository file.
    """

    fix = state["fix"]

    repo_path = state["repo_path"]

    print("\n========== GENERATED FIX ==========")
    print(f"Target file: {fix.file_path}")
    print("Generated diff:")
    print(fix.diff)
    print("===================================\n")

    validation = patch_validator.validate(
        repo_path=repo_path,
        file_path=fix.file_path,
        diff=fix.diff,
    )

    print(
       "🛡️ Patch Validator"
    )

    if validation["valid"]:

        print(
            "✅ Patch matches the target file."
        )

    else:

        print(
            "❌ Patch does not match the target file."
        )

    return {
        "patch_validation": validation,
    }


# =========================================================
# PATCH VALIDATION ROUTER
# =========================================================

def patch_validation_router(state: DevGuardianState):
    """
    Decide what happens after patch validation.
    """

    validation = state["patch_validation"]

    if validation["valid"]:

        return "valid"

    return "invalid"


# =========================================================
# PATCH INVALID → HUMAN REVIEW
# =========================================================

def patch_human_review_node(state: DevGuardianState):
    """
    Stop automatic remediation when the patch is invalid.
    """

    print(
        "👤 LangGraph -> Human Review"
    )

    print(
        "❌ Patch validation failed."
    )

    return {
        "remediation": {
            "status": "human_review",
            "message": (
                "The AI-generated patch does not match "
                "the current target file. "
                "Human review is required."
            ),
        }
    }


# =========================================================
# SAFETY CHECKER NODE
# =========================================================

def safety_checker_node(state: DevGuardianState):
    """
    Check whether the generated fix is safe.
    """

    fix = state["fix"]

    safety = safety_checker.check(
        fix
    )

    return {
        "safety": safety,
    }


# =========================================================
# SAFETY ROUTER
# =========================================================

def safety_router(state: DevGuardianState):
    """
    Decide whether automatic remediation is allowed.
    """

    safety = state["safety"]

    if (
        safety["safe"]
        and not safety["requires_human_review"]
    ):

        return "approved"

    return "human_review"


# =========================================================
# GITHUB REMEDIATION NODE
# =========================================================

def github_remediation_node(state: DevGuardianState):
    """
    Execute GitHub remediation.

    Flow:

        Create branch
             ↓
        Apply patch
             ↓
        Commit
             ↓
        Create PR
             ↓
        Save PR result to Incident
    """

    print(
        "🚀 LangGraph -> GitHub Remediation"
    )

    owner = state["repo_owner"]

    repo = state["repo_name"]

    base_branch = state["base_branch"]

    # ---------------------------------------------------------
    # M6 — Get Incident ID
    # ---------------------------------------------------------

    incident_id = state.get(
        "incident_id"
    )

    print(
        f"🗃️ Incident ID: {incident_id}"
    )

    # ---------------------------------------------------------
    # Create unique branch
    # ---------------------------------------------------------

    branch_name = (
        f"devguardian/auto-fix-{int(time.time())}"
    )

    # ---------------------------------------------------------
    # GitHub API
    # ---------------------------------------------------------

    github = GitHubAPI(
        settings.GITHUB_TOKEN
    )

    # ---------------------------------------------------------
    # Remediation service
    # ---------------------------------------------------------

    remediation_service = GitHubRemediation(
        github
    )

    # ---------------------------------------------------------
    # Execute remediation with retries
    # ---------------------------------------------------------

    result = run_with_retries(
        lambda: remediation_service.remediate(
            owner=owner,
            repo=repo,
            fix=state["fix"],
            base_branch=base_branch,
            branch_name=branch_name,
        ),
        "GitHub Remediation",
    )

    # =========================================================
    # M6 — SAVE PR RESULT TO INCIDENT
    # =========================================================

    if incident_id is not None:

        db = SessionLocal()

        try:

            incident = db.get(
                Incident,
                incident_id,
            )

            if incident is None:

                print(
                    f"⚠️ Incident {incident_id} "
                    f"not found in database."
                )

            else:

                # -------------------------------------------------
                # PR CREATED SUCCESSFULLY
                # -------------------------------------------------

                if result.get("success"):

                    incident.pr_number = (
                        result.get("pr_number")
                    )

                    incident.pr_status = "open"

                    print(
                        f"📝 Incident {incident_id} "
                        f"updated with PR "
                        f"#{incident.pr_number}"
                    )

                    print(
                        f"🔗 PR URL: "
                        f"{result.get('pr_url')}"
                    )

                # -------------------------------------------------
                # PR CREATION FAILED
                # -------------------------------------------------

                else:

                    incident.pr_status = "failed"

                    print(
                        f"⚠️ Incident {incident_id} "
                        f"PR status marked as failed."
                    )

                db.commit()

        except Exception as e:

            db.rollback()

            print(
                f"❌ Failed to save PR result "
                f"to Incident {incident_id}: {e}"
            )

        finally:

            db.close()

    # =========================================================
    # SUCCESS
    # =========================================================

    if result.get("success"):

        print(
            "✅ GitHub remediation completed."
        )

        if result.get("pr_url"):

            print(
                f"🔗 Pull Request: "
                f"{result['pr_url']}"
            )

    # =========================================================
    # FAILURE
    # =========================================================

    else:

        print(
            "❌ GitHub remediation failed."
        )

    return {
        "remediation": result,
    }


# =========================================================
# SAFETY → HUMAN REVIEW
# =========================================================

def safety_human_review_node(state: DevGuardianState):
    """
    Stop automatic remediation when the fix is unsafe.
    """

    print(
        "👤 LangGraph -> Human Review"
    )

    print(
        "❌ Safety check failed."
    )

    return {
        "remediation": {
            "status": "human_review",
            "message": (
                "Fix failed the safety checks "
                "and requires human review."
            ),
        }
    }


# =========================================================
# BUILD GRAPH
# =========================================================

builder = StateGraph(
    DevGuardianState
)


# =========================================================
# REGISTER NODES
# =========================================================

builder.add_node(
    "router",
    router_node,
)

builder.add_node(
    "ci_agent",
    ci_agent_node,
)

builder.add_node(
    "docker_agent",
    docker_agent_node,
)

builder.add_node(
    "kubernetes_agent",
    kubernetes_agent_node,
)

# M6 — Incident Memory

builder.add_node(
    "incident_memory",
    incident_memory_node,
)

builder.add_node(
    "fix_agent",
    fix_agent_node,
)

builder.add_node(
    "patch_validator",
    patch_validator_node,
)

builder.add_node(
    "safety_checker",
    safety_checker_node,
)

builder.add_node(
    "github_remediation",
    github_remediation_node,
)

builder.add_node(
    "patch_human_review",
    patch_human_review_node,
)

builder.add_node(
    "safety_human_review",
    safety_human_review_node,
)


# =========================================================
# START → ROUTER
# =========================================================

builder.add_edge(
    START,
    "router",
)


# =========================================================
# ROUTER → DIAGNOSIS AGENT
# =========================================================

builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "ci": "ci_agent",
        "docker": "docker_agent",
        "kubernetes": "kubernetes_agent",
    },
)


# =========================================================
# DIAGNOSIS → INCIDENT MEMORY
# =========================================================

builder.add_edge(
    "ci_agent",
    "incident_memory",
)

builder.add_edge(
    "docker_agent",
    "incident_memory",
)

builder.add_edge(
    "kubernetes_agent",
    "incident_memory",
)


# =========================================================
# INCIDENT MEMORY → FIX
# =========================================================

builder.add_edge(
    "incident_memory",
    "fix_agent",
)


# =========================================================
# FIX → PATCH VALIDATION
# =========================================================

builder.add_edge(
    "fix_agent",
    "patch_validator",
)


# =========================================================
# PATCH VALIDATION → DECISION
# =========================================================

builder.add_conditional_edges(
    "patch_validator",
    patch_validation_router,
    {
        "valid": "safety_checker",
        "invalid": "patch_human_review",
    },
)


# =========================================================
# SAFETY → DECISION
# =========================================================

builder.add_conditional_edges(
    "safety_checker",
    safety_router,
    {
        "approved": "github_remediation",
        "human_review": "safety_human_review",
    },
)


# =========================================================
# FINAL NODES → END
# =========================================================

builder.add_edge(
    "github_remediation",
    END,
)

builder.add_edge(
    "patch_human_review",
    END,
)

builder.add_edge(
    "safety_human_review",
    END,
)


# =========================================================
# POSTGRES CONNECTION POOL
# =========================================================

connection_pool = ConnectionPool(
    conninfo=settings.SYNC_DATABASE_URL,
    max_size=20,
    kwargs={
        "autocommit": True,
        "row_factory": dict_row,
    },
    open=True,
)


# =========================================================
# POSTGRES CHECKPOINTER
# =========================================================

postgres_checkpointer = PostgresSaver(
    connection_pool
)


# =========================================================
# CREATE LANGGRAPH CHECKPOINT TABLES
# =========================================================

postgres_checkpointer.setup()


# =========================================================
# COMPILE GRAPH
# =========================================================

graph = builder.compile(
    checkpointer=postgres_checkpointer
)