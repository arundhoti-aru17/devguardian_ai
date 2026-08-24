import asyncio
import hmac
import hashlib
import io
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Request, Header, HTTPException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

from app.db.session import SessionLocal
from app.db.models import Incident

from app.services.github_events import dispatch_event
from app.services.github_api import GitHubAPI
from app.services.incident_feedback import IncidentFeedbackService
from app.services.log_reader import LogReader
from app.services.repository_checkout import RepositoryCheckout

from app.core.config import settings
from app.graph.workflow import graph


router = APIRouter()


# =========================================================
# GITHUB WEBHOOK
# =========================================================

@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default="Unknown"),
):
    """
    Receive GitHub webhook events.

    Handles:

        workflow_run
            ↓
        Failed workflow
            ↓
        DevGuardian LangGraph

    AND:

        pull_request
            ↓
        PR closed / merged
            ↓
        IncidentFeedbackService
            ↓
        Update Incident feedback
    """

    # =====================================================
    # 1. READ GITHUB PAYLOAD
    # =====================================================
    raw_body = await request.body()   # bytes, only used for signature verification
    payload = await request.json()

    logger.info("GitHub Webhook Received")

    # =====================================================
    # 1B. VERIFY WEBHOOK SIGNATURE (OPTIONAL but RECOMMENDED)
    # =====================================================

    signature = request.headers.get("X-Hub-Signature-256")
    if signature:
        sig_parts = signature.split("=")
        if len(sig_parts) == 2:
            algorithm = sig_parts[0]
            received_sig = sig_parts[1]

            if algorithm == "sha256":
                mac = hmac.new(
                    settings.GITHUB_WEBHOOK_SECRET.encode(),
                    raw_body,
                    hashlib.sha256,
                ).hexdigest()
                if not hmac.compare_digest(mac, received_sig):
                    print("❌ Webhook signature mismatch!")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid GitHub webhook signature.",
                    )
                print("✅ Webhook signature verified.")
            else:
                print(f"⚠️ Unsupported signature algorithm: {algorithm}")
        else:
            print("⚠️ Malformed webhook signature header")
    else:
        print("⚠️ No webhook signature received (X-Hub-Signature-256)")

    print("\n📨 GitHub Webhook Received")
    print(f"Event: {x_github_event}")

    # =====================================================
    # 2. DISPATCH EVENT
    # =====================================================

    event_data = dispatch_event(
        event=x_github_event,
        payload=payload,
    )

    print("Event data:")
    print(event_data)

    # =====================================================
    # 3. EXTRACT REPOSITORY INFORMATION
    # =====================================================

    repository = payload.get(
        "repository",
        {},
    )

    repo_owner = (
        repository
        .get("owner", {})
        .get("login")
    )

    repo_name = repository.get(
        "name"
    )

    # =====================================================
    # 4. HANDLE PULL REQUEST EVENTS
    # =====================================================

    if x_github_event == "pull_request":

        action = payload.get(
            "action"
        )

        pull_request = payload.get(
            "pull_request",
            {}
        )

        pr_number = pull_request.get(
            "number"
        )

        merged = pull_request.get(
            "merged",
            False
        )

        print(
            "\n🔀 Pull Request Event"
        )

        print(
            f"   Action: {action}"
        )

        print(
            f"   PR Number: #{pr_number}"
        )

        print(
            f"   Merged: {merged}"
        )

        # -------------------------------------------------
        # We only process closed PRs.
        #
        # A merged PR is also closed on GitHub.
        # -------------------------------------------------

        if action != "closed":

            print(
                "ℹ️ Pull Request is not closed yet. "
                "No feedback update required."
            )

            return {
                "message": (
                    "Pull Request event received."
                ),
                "event": x_github_event,
                "action": action,
            }

        # -------------------------------------------------
        # Validate repository
        # -------------------------------------------------

        if not repo_owner:

            print(
                "⚠️ Repository owner missing."
            )

            return {
                "error": (
                    "Repository owner missing "
                    "from webhook payload."
                )
            }

        if not repo_name:

            print(
                "⚠️ Repository name missing."
            )

            return {
                "error": (
                    "Repository name missing "
                    "from webhook payload."
                )
            }

        # -------------------------------------------------
        # Validate PR number
        # -------------------------------------------------

        if not pr_number:

            print(
                "⚠️ Pull Request number missing."
            )

            return {
                "error": (
                    "Pull Request number missing."
                )
            }

        # -------------------------------------------------
        # Find Incident associated with PR
        # -------------------------------------------------

        db = SessionLocal()

        try:

            incident = (
                db.query(Incident)
                .filter(
                    Incident.pr_number == pr_number,
                    Incident.repository
                    == f"{repo_owner}/{repo_name}",
                )
                .first()
            )

            if incident is None:

                print(
                    f"ℹ️ No DevGuardian Incident found "
                    f"for PR #{pr_number}."
                )

                return {
                    "message": (
                        "No DevGuardian Incident "
                        "associated with this PR."
                    ),
                    "event": x_github_event,
                    "pr_number": pr_number,
                }

            incident_id = incident.id

            print(
                f"🗃️ Incident found: #{incident_id}"
            )

        except Exception as e:

            print(
                f"❌ Failed to find Incident "
                f"for PR #{pr_number}: {e}"
            )

            return {
                "error": (
                    "Failed to find Incident "
                    "associated with PR."
                ),
                "details": str(e),
            }

        finally:

            db.close()

        # -------------------------------------------------
        # Update Incident feedback
        # -------------------------------------------------

        print(
            "\n🧠 Updating Incident feedback..."
        )

        feedback_service = (
            IncidentFeedbackService()
        )

        result = (
            feedback_service
            .update_incident_feedback(
                incident_id
            )
        )

        print(
            "✅ PR feedback processing completed."
        )

        return {
            "message": (
                "Pull Request feedback processed."
            ),
            "event": x_github_event,
            "action": action,
            "repository": (
                f"{repo_owner}/{repo_name}"
            ),
            "pr_number": pr_number,
            "incident_id": incident_id,
            "feedback_result": result,
        }

    # =====================================================
    # 5. EXTRACT WORKFLOW INFORMATION
    # =====================================================

    workflow_run = payload.get(
        "workflow_run",
        {},
    )

    run_id = workflow_run.get(
        "id"
    )

    branch = workflow_run.get(
        "head_branch"
    )

    workflow_name = workflow_run.get(
        "name",
        "Unknown",
    )

    status = workflow_run.get(
        "status"
    )

    conclusion = workflow_run.get(
        "conclusion"
    )

    # =====================================================
    # 6. IGNORE NON-WORKFLOW EVENTS
    # =====================================================

    if x_github_event != "workflow_run":

        return {
            "message": "GitHub event received.",
            "event": x_github_event,
        }

    # =====================================================
    # 7. IGNORE DEVGUARDIAN REMEDIATION BRANCHES
    # =====================================================

    # DevGuardian creates branches such as:
    #
    #     devguardian/auto-fix-1786704555
    #
    # Those branches trigger GitHub Actions themselves.
    # We must NOT analyze failures from those branches,
    # otherwise DevGuardian can trigger itself repeatedly.
    #
    # Only real user/source branches should enter the
    # DevGuardian analysis pipeline.

    if (
        x_github_event == "workflow_run"
        and branch
        and branch.startswith("devguardian/auto-fix-")
    ):
        print(
            "ℹ️ Ignoring DevGuardian remediation branch: "
            f"{branch}"
        )

        return {
            "message": (
                "DevGuardian remediation branch ignored."
            ),
            "event": x_github_event,
            "branch": branch,
            "reason": "devguardian_remediation_branch",
        }


    # =====================================================
    # 8. IGNORE SUCCESSFUL WORKFLOWS
    # =====================================================

    if not (
        status == "completed"
        and conclusion == "failure"
    ):

        print(
            "ℹ️ Workflow did not fail. "
            "No DevGuardian analysis required."
        )

        return {
            "message": "Workflow did not fail.",
            "event": x_github_event,
            "status": status,
            "conclusion": conclusion,
        }

    # =====================================================
    # 8. VALIDATE REQUIRED INFORMATION
    # =====================================================

    if not repo_owner:

        return {
            "error": (
                "Repository owner missing "
                "from webhook payload."
            )
        }

    if not repo_name:

        return {
            "error": (
                "Repository name missing "
                "from webhook payload."
            )
        }

    if not run_id:

        return {
            "error": (
                "Workflow run ID missing "
                "from webhook payload."
            )
        }

    if not branch:

        return {
            "error": (
                "Workflow branch missing "
                "from webhook payload."
            )
        }

    # =====================================================
    # 9. SAVE INCIDENT / PREVENT DUPLICATES
    # =====================================================

    db = SessionLocal()

    incident_id = None
    duplicate_incident = False
    active_remediation = False

    try:

        # -------------------------------------------------
        # CHECK 1:
        # Has this exact GitHub workflow run already
        # been processed?
        # -------------------------------------------------

        existing_incident = (
            db.query(Incident)
            .filter(
                Incident.workflow_run_id == run_id
            )
            .first()
        )

        if existing_incident:

            incident_id = existing_incident.id
            duplicate_incident = True

            print(
                f"♻️ Incident already exists "
                f"for workflow run {run_id}."
            )

            print(
                f"   Existing incident ID: "
                f"{incident_id}"
            )

        else:

            # -------------------------------------------------
            # CHECK 2:
            # Does this repository + branch + workflow already
            # have an OPEN DevGuardian remediation PR?
            #
            # This prevents:
            #
            # failure -> incident -> PR
            # failure -> incident -> PR
            # failure -> incident -> PR
            #
            # when the original broken branch keeps producing
            # workflow_run failure events.
            # -------------------------------------------------

            existing_active_remediation = (
                db.query(Incident)
                .filter(
                    Incident.repository
                    == f"{repo_owner}/{repo_name}",

                    Incident.branch == branch,

                    Incident.workflow == workflow_name,

                    Incident.pr_status == "open",

                    Incident.pr_number.isnot(None),
                )
                .order_by(
                    Incident.id.desc()
                )
                .first()
            )

            if existing_active_remediation:

                active_remediation = True

                print(
                    "\n🛑 Active DevGuardian remediation "
                    "already exists."
                )

                print(
                    f"   Existing incident: "
                    f"{existing_active_remediation.id}"
                )

                print(
                    f"   Existing PR: "
                    f"#{existing_active_remediation.pr_number}"
                )

                print(
                    f"   Repository: "
                    f"{repo_owner}/{repo_name}"
                )

                print(
                    f"   Branch: {branch}"
                )

                print(
                    "⏭️ Skipping duplicate failure."
                )

            else:

                # -------------------------------------------------
                # No existing active remediation.
                # Create a new incident.
                # -------------------------------------------------

                incident = Incident(
                    repository=(
                        f"{repo_owner}/{repo_name}"
                    ),
                    branch=branch or "Unknown",
                    workflow=workflow_name,
                    status=status or "Unknown",
                    workflow_run_id=run_id,
                )

                db.add(
                    incident
                )

                db.commit()

                db.refresh(
                    incident
                )

                incident_id = incident.id

                print(
                    "✅ New incident saved successfully."
                )

                print(
                    f"   Incident ID: {incident_id}"
                )

                print(
                    f"   Workflow Run ID: {run_id}"
                )

    except Exception as e:

        db.rollback()

        print(
            f"❌ Failed to save incident: {e}"
        )

        return {
            "error": (
                "Failed to save incident."
            ),
            "details": str(e),
        }

    finally:

        db.close()

    # =====================================================
    # PREVENT DUPLICATE PROCESSING
    # =====================================================

    if duplicate_incident:

        return {
            "message": (
                "This GitHub workflow run was "
                "already processed. "
                "No duplicate incident created."
            ),
            "event": x_github_event,
            "repository": (
                f"{repo_owner}/{repo_name}"
            ),
            "branch": branch,
            "run_id": run_id,
            "incident_id": incident_id,
        }

    # =====================================================
    # PREVENT DUPLICATE ACTIVE REMEDIATION
    # =====================================================

    if active_remediation:

        return {
            "message": (
                "An active DevGuardian remediation "
                "already exists for this branch. "
                "No duplicate incident or PR created."
            ),
            "event": x_github_event,
            "repository": (
                f"{repo_owner}/{repo_name}"
            ),
            "branch": branch,
            "workflow": workflow_name,
            "reason": "active_remediation_exists",
        }

    # =====================================================
    # 10. DISPATCH BACKGROUND PROCESSING
    # =====================================================

    print(
        "\n🚨 Failed workflow detected!"
    )

    print(
        f"Repository: "
        f"{repo_owner}/{repo_name}"
    )

    print(
        f"Branch: {branch}"
    )

    print(
        f"Run ID: {run_id}"
    )

    asyncio.create_task(
        process_failed_workflow(
            incident_id=incident_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            branch=branch,
            run_id=run_id,
            workflow_name=workflow_name,
            status=status,
            conclusion=conclusion,
        )
    )

    return {
        "message": (
            "GitHub workflow failure received. "
            "DevGuardian analysis started in background."
        ),
        "event": x_github_event,
        "repository": (
            f"{repo_owner}/{repo_name}"
        ),
        "branch": branch,
        "run_id": run_id,
        "workflow": workflow_name,
        "status": status,
        "conclusion": conclusion,
        "incident_id": incident_id,
    }


# =========================================================
# BACKGROUND PIPELINE
# =========================================================

async def process_failed_workflow(
    incident_id,
    repo_owner: str,
    repo_name: str,
    branch: str,
    run_id: int,
    workflow_name: str,
    status: str,
    conclusion: str,
):
    """
    Background processing pipeline for a failed GitHub
    Actions workflow.

    Normal case:

        workflow failure
              ↓
        workflow logs
              ↓
        repository
              ↓
        LangGraph
              ↓
        Fix Agent
              ↓
        Patch Validator
              ↓
        Safety Checker
              ↓
        GitHub Remediation

    Configuration-error fallback:

        workflow failure
              ↓
        workflow logs unavailable
              ↓
        repository
              ↓
        inspect .github/workflows
              ↓
        LangGraph
              ↓
        Fix Agent
              ↓
        Patch Validator
              ↓
        Safety Checker
              ↓
        GitHub Remediation

    The important point is that unavailable workflow logs
    do NOT automatically terminate the DevGuardian pipeline.
    """

    github = GitHubAPI(
        settings.GITHUB_TOKEN
    )

    # =====================================================
    # 11. DOWNLOAD WORKFLOW LOGS
    # =====================================================

    print(
        "\n⬇️ Downloading workflow logs..."
    )

    logs_zip = None
    combined_logs = ""
    logs_available = False

    try:

        logs_zip = await asyncio.to_thread(
            github.download_workflow_logs,
            owner=repo_owner,
            repo=repo_name,
            run_id=run_id,
        )

        logs_available = True

        print(
            "✅ Workflow logs downloaded."
        )

    except Exception as e:

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT stop the pipeline here.
        #
        # A failed workflow_run may have no jobs when the
        # workflow configuration itself is invalid.
        #
        # In that situation GitHub may return:
        #
        #     workflow_run = failure
        #     jobs = 0
        #     logs = 404
        #
        # We therefore continue with repository analysis.
        # -------------------------------------------------

        print(
            f"⚠️ Workflow logs unavailable: {e}"
        )

        print(
            "🔄 Continuing with repository-based diagnosis..."
        )

    # =====================================================
    # 12. DOWNLOAD REPOSITORY
    # =====================================================

    print(
        "\n⬇️ Downloading repository..."
    )

    try:

        repository_archive = await asyncio.to_thread(
            github.download_repository_archive,
            owner=repo_owner,
            repo=repo_name,
            branch=branch,
        )

    except Exception as e:

        print(
            f"❌ Failed to download repository archive: {e}"
        )

        _mark_incident_failed(
            incident_id,
            f"repo_download_failed: {e}",
        )

        return

    print(
        "✅ Repository archive downloaded."
    )

    # =====================================================
    # 13. CREATE TEMPORARY DIRECTORY
    # =====================================================

    with tempfile.TemporaryDirectory(
        prefix="devguardian_webhook_"
    ) as temp_directory:

        temp_root = Path(
            temp_directory
        )

        # =================================================
        # 14. EXTRACT WORKFLOW LOGS IF AVAILABLE
        # =================================================

        if logs_available and logs_zip:

            logs_directory = (
                temp_root / "logs"
            )

            logs_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            print(
                "📦 Extracting workflow logs..."
            )

            try:

                with zipfile.ZipFile(
                    io.BytesIO(logs_zip)
                ) as archive:

                    archive.extractall(
                        logs_directory
                    )

                log_reader = LogReader()

                combined_logs = (
                    log_reader.read_logs(
                        str(logs_directory)
                    )
                )

                print(
                    "✅ Workflow logs loaded."
                )

            except Exception as e:

                print(
                    f"⚠️ Failed to extract workflow logs: {e}"
                )

                print(
                    "🔄 Continuing with "
                    "repository-based diagnosis..."
                )

                combined_logs = ""

        # =================================================
        # 15. EXTRACT REPOSITORY
        # =================================================

        print(
            "📦 Extracting repository..."
        )

        try:

            repository_checkout = (
                RepositoryCheckout()
            )

            repo_path = await asyncio.to_thread(
                repository_checkout.checkout,
                repository_archive,
            )

        except Exception as e:

            print(
                f"❌ Failed to check out repository: {e}"
            )

            _mark_incident_failed(
                incident_id,
                f"repo_checkout_failed: {e}",
            )

            return

        print(
            f"📁 Repository ready: {repo_path}"
        )

        # =================================================
        # 16. FALLBACK DIAGNOSTIC CONTEXT
        # =================================================
        #
        # If workflow logs are unavailable, inspect the
        # actual GitHub Actions workflow files.
        #
        # This allows DevGuardian to diagnose configuration
        # errors such as malformed workflow YAML or invalid
        # workflow structure.
        # =================================================

        if not combined_logs:

            print(
                "\n🔎 Workflow logs unavailable."
            )

            print(
                "🧠 Building fallback diagnostic context "
                "from repository workflow files..."
            )

            fallback_parts = []

            fallback_parts.append(
                "DEVGUARDIAN FALLBACK DIAGNOSTIC CONTEXT\n"
            )

            fallback_parts.append(
                f"Repository: "
                f"{repo_owner}/{repo_name}\n"
            )

            fallback_parts.append(
                f"Branch: {branch}\n"
            )

            fallback_parts.append(
                f"Workflow: {workflow_name}\n"
            )

            fallback_parts.append(
                f"Workflow Run ID: {run_id}\n"
            )

            fallback_parts.append(
                f"Status: {status}\n"
            )

            fallback_parts.append(
                f"Conclusion: {conclusion}\n"
            )

            fallback_parts.append(
                "\nIMPORTANT:\n"
                "GitHub reported the workflow run as failed, "
                "but workflow execution logs were unavailable. "
                "The repository workflow configuration should "
                "therefore be inspected directly for configuration "
                "or syntax problems.\n"
            )

            # ---------------------------------------------
            # Locate workflow directory
            # ---------------------------------------------

            workflows_directory = (
                Path(repo_path)
                / ".github"
                / "workflows"
            )

            if workflows_directory.exists():

                workflow_files = list(
                    workflows_directory.glob("*")
                )

                print(
                    f"🔎 Found "
                    f"{len(workflow_files)} workflow file(s)."
                )

                for workflow_file in workflow_files:

                    if not workflow_file.is_file():
                        continue

                    # Only inspect YAML workflow files.

                    if workflow_file.suffix.lower() not in {
                        ".yml",
                        ".yaml",
                    }:
                        continue

                    print(
                        f"📄 Reading workflow: "
                        f"{workflow_file.name}"
                    )

                    try:

                        workflow_content = (
                            workflow_file.read_text(
                                encoding="utf-8"
                            )
                        )

                        fallback_parts.append(
                            "\n\n"
                            f"========== WORKFLOW FILE: "
                            f"{workflow_file.name} "
                            f"==========\n\n"
                        )

                        fallback_parts.append(
                            workflow_content
                        )

                    except Exception as e:

                        print(
                            f"⚠️ Could not read "
                            f"{workflow_file}: {e}"
                        )

            else:

                print(
                    "⚠️ No .github/workflows directory found."
                )

                fallback_parts.append(
                    "\nNo .github/workflows directory "
                    "was found in the repository.\n"
                )

            combined_logs = "".join(
                fallback_parts
            )

            print(
                "✅ Fallback diagnostic context created."
            )

        # =================================================
        # 17. BUILD DYNAMIC DEVGUARDIAN STATE
        # =================================================

        graph_state = {

            # -------------------------------------------------
            # Failure information
            # -------------------------------------------------

            "logs": combined_logs,

            # -------------------------------------------------
            # Repository information
            # -------------------------------------------------

            "repo_path": repo_path,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "base_branch": branch,

            # -------------------------------------------------
            # GitHub Actions
            # -------------------------------------------------

            "run_id": run_id,

            # -------------------------------------------------
            # M6 — INCIDENT CONNECTION
            # -------------------------------------------------

            "incident_id": incident_id,

            # -------------------------------------------------
            # GRAPH STATE
            # -------------------------------------------------

            "route": "",
            "diagnosis": None,
            "memory_context": None,
            "fix": None,
            "patch_validation": None,
            "safety": None,
            "remediation": None,
        }

        print(
            "\n🧠 Starting DevGuardian LangGraph..."
        )

        print(
            f"   Incident ID: {incident_id}"
        )

        # =================================================
        # 18. RUN LANGGRAPH
        # =================================================

        try:

            result = await asyncio.to_thread(
                graph.invoke,
                graph_state,
                config={
                    "configurable": {
                        "thread_id": (
                            f"incident-{incident_id}"
                        )
                    }
                },
            )

        except Exception as e:

            print(
                f"❌ LangGraph pipeline failed: {e}"
            )

            _mark_incident_failed(
                incident_id,
                f"graph_pipeline_failed: {e}",
            )

            return

        print(
            "\n✅ DevGuardian LangGraph completed."
        )

        # =================================================
        # 19. PERSIST RESULT
        # =================================================

        _mark_incident_completed(
            incident_id,
            result,
        )


# =========================================================
# DB HELPERS
# =========================================================

def _mark_incident_failed(
    incident_id,
    reason: str,
):
    """
    Mark an incident as failed when one of the background
    processing stages fails.
    """

    if incident_id is None:

        print(
            f"⚠️ No incident_id to update. "
            f"Reason: {reason}"
        )

        return

    db = SessionLocal()

    try:

        incident = db.get(
            Incident,
            incident_id,
        )

        if incident:

            incident.status = "failed"

            incident.error_message = reason

            db.commit()

            print(
                f"🗃️ Incident {incident_id} "
                f"marked failed: {reason}"
            )

    except Exception as e:

        db.rollback()

        print(
            f"❌ Failed to update incident "
            f"{incident_id}: {e}"
        )

    finally:

        db.close()


def _mark_incident_completed(
    incident_id,
    result: dict,
):
    """
    Persist the completed LangGraph result into the Incident.

    M6 stores:

        failure_type
        root_cause
        fix_description
        outcome
        embedding
    """

    if incident_id is None:

        print(
            f"⚠️ No incident_id to update. "
            f"Result: {result}"
        )

        return

    db = SessionLocal()

    try:

        # =================================================
        # 1. FIND INCIDENT
        # =================================================

        incident = db.get(
            Incident,
            incident_id,
        )

        if not incident:

            print(
                f"⚠️ Incident {incident_id} "
                f"not found."
            )

            return

        # =================================================
        # 2. MARK AS DIAGNOSED
        # =================================================

        incident.status = "diagnosed"

        # =================================================
        # 3. EXTRACT DIAGNOSIS
        # =================================================

        diagnosis = result.get(
            "diagnosis"
        )

        if diagnosis:

            if isinstance(
                diagnosis,
                dict,
            ):

                incident.failure_type = (
                    diagnosis.get(
                        "failure_type"
                    )
                )

                incident.root_cause = (
                    diagnosis.get(
                        "root_cause"
                    )
                )

            else:

                incident.failure_type = getattr(
                    diagnosis,
                    "failure_type",
                    None,
                )

                incident.root_cause = getattr(
                    diagnosis,
                    "root_cause",
                    None,
                )

        # =================================================
        # 4. EXTRACT FIX INFORMATION
        # =================================================

        fix = result.get(
            "fix"
        )

        if fix:

            if isinstance(
                fix,
                dict,
            ):

                incident.fix_description = (
                    fix.get(
                        "explanation"
                    )
                )

            else:

                incident.fix_description = getattr(
                    fix,
                    "explanation",
                    None,
                )

        # =================================================
        # 5. DETERMINE OUTCOME
        # =================================================

        patch_validation = result.get(
            "patch_validation"
        )

        remediation = result.get(
            "remediation"
        )

        if (
            isinstance(
                patch_validation,
                dict,
            )
            and patch_validation.get(
                "valid"
            ) is True
        ):

            incident.outcome = "validated"

        elif (
            isinstance(
                remediation,
                dict,
            )
            and remediation.get(
                "status"
            ) == "human_review"
        ):

            incident.outcome = "human_review"

        else:

            incident.outcome = "diagnosed"

        # =================================================
        # 6. BUILD EMBEDDING TEXT
        # =================================================

        embedding_text = (
            f"Failure type: "
            f"{incident.failure_type or ''}\n"
            f"Root cause: "
            f"{incident.root_cause or ''}\n"
            f"Fix: "
            f"{incident.fix_description or ''}\n"
            f"Outcome: "
            f"{incident.outcome or ''}"
        )

        print(
            "\n🧠 Generating incident embedding..."
        )

        # =================================================
        # 7. GENERATE EMBEDDING
        # =================================================

        from app.services.embedding_service import (
            EmbeddingService
        )

        embedding_service = (
            EmbeddingService()
        )

        embedding = (
            embedding_service.generate_embedding(
                embedding_text
            )
        )

        # =================================================
        # 8. STORE EMBEDDING
        # =================================================

        incident.embedding = embedding

        # =================================================
        # 9. PERSIST EVERYTHING
        # =================================================

        db.add(
            incident
        )

        db.commit()

        db.refresh(
            incident
        )

        # =================================================
        # 10. PRINT CONFIRMATION
        # =================================================

        print(
            f"\n🧠 Incident {incident_id} "
            f"saved with M6 memory."
        )

        print(
            f"   Failure type: "
            f"{incident.failure_type}"
        )

        print(
            f"   Root cause: "
            f"{incident.root_cause}"
        )

        print(
            f"   Fix: "
            f"{incident.fix_description}"
        )

        print(
            f"   Outcome: "
            f"{incident.outcome}"
        )

        print(
            f"   Embedding dimensions: "
            f"{len(incident.embedding)}"
        )

    except Exception as e:

        db.rollback()

        print(
            f"❌ Failed to update incident "
            f"{incident_id}: {e}"
        )

    finally:

        db.close()