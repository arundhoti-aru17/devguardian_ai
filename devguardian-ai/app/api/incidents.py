from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Incident
from app.services.incident_memory import IncidentMemory


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)

incident_memory = IncidentMemory()


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# GET INCIDENT STATISTICS
# =========================================================

@router.get("/stats")
def get_incident_stats(
    db: Session = Depends(get_db),
):
    """
    Return summary statistics for the DevGuardian dashboard.
    """

    incidents = (
        db.query(Incident)
        .order_by(Incident.id.desc())
        .all()
    )

    total_incidents = len(incidents)

    # Incidents where DevGuardian successfully produced
    # an accepted/merged remediation.
    resolved_incidents = sum(
        1
        for incident in incidents
        if incident.outcome == "accepted"
        and incident.pr_status == "merged"
    )

    # Currently open AI-generated PRs.
    open_prs = sum(
        1
        for incident in incidents
        if incident.pr_number is not None
        and incident.pr_status == "open"
    )

    # Accepted resolutions.
    accepted_incidents = sum(
        1
        for incident in incidents
        if incident.feedback == "accepted"
    )

    # Rejected feedback.
    rejected_incidents = sum(
        1
        for incident in incidents
        if incident.feedback == "rejected"
    )

    # Human-review cases.
    human_review_incidents = sum(
        1
        for incident in incidents
        if incident.outcome == "human_review"
    )

    # Calculate success rate.
    #
    # We only calculate this when there is feedback
    # available. This prevents old unresolved incidents
    # from artificially lowering the percentage.
    feedback_count = accepted_incidents + rejected_incidents

    if feedback_count > 0:
        success_rate = round(
            (accepted_incidents / feedback_count) * 100,
            2,
        )
    else:
        success_rate = 0

    return {
        "success": True,
        "stats": {
            "total_incidents": total_incidents,
            "resolved_incidents": resolved_incidents,
            "open_prs": open_prs,
            "accepted_incidents": accepted_incidents,
            "rejected_incidents": rejected_incidents,
            "human_review_incidents": human_review_incidents,
            "success_rate": success_rate,
        },
    }


# =========================================================
# GET ALL INCIDENTS
# =========================================================

@router.get("")
def get_incidents(
    db: Session = Depends(get_db),
):
    """
    Return recent DevGuardian incidents.

    Note: similar_incidents is intentionally omitted here.
    Computing embeddings/similarity for every row on every list
    load would be expensive - it's only computed on the detail
    endpoint below, where a single incident is being viewed.
    """

    incidents = (
        db.query(Incident)
        .order_by(Incident.id.desc())
        .all()
    )

    return {
        "success": True,
        "count": len(incidents),
        "incidents": [
            {
                "id": incident.id,
                "repository": incident.repository,
                "branch": incident.branch,
                "workflow": incident.workflow,
                "status": incident.status,
                "created_at": (
                    incident.created_at.isoformat()
                    if incident.created_at
                    else None
                ),
                "workflow_run_id": incident.workflow_run_id,
                "failure_type": incident.failure_type,
                "root_cause": incident.root_cause,
                "fix_description": incident.fix_description,
                "outcome": incident.outcome,
                "pr_number": incident.pr_number,
                "pr_status": incident.pr_status,
                "feedback": incident.feedback,
                "target_file": incident.target_file,
            }
            for incident in incidents
        ],
    }


# =========================================================
# GET ONE INCIDENT
# =========================================================

@router.get("/{incident_id}")
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a single DevGuardian incident, including any
    similar previous incidents found via embedding search.
    """

    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found.",
        )

    # -----------------------------------------------------
    # Only bother searching for matches if this incident
    # actually has an embedding stored.
    # -----------------------------------------------------

    similar_incidents = []

    if incident.embedding is not None:
        matches = incident_memory.find_similar_incidents_with_scores(
            db,
            incident,
            limit=1,
        )

        similar_incidents = [
            {
                "id": matched_incident.id,
                "failure_type": matched_incident.failure_type,
                "fix_description": matched_incident.fix_description,
                "outcome": matched_incident.outcome,
                "similarity": similarity,
            }
            for matched_incident, similarity in matches
        ]

    return {
        "success": True,
        "incident": {
            "id": incident.id,
            "repository": incident.repository,
            "branch": incident.branch,
            "workflow": incident.workflow,
            "status": incident.status,
            "created_at": (
                incident.created_at.isoformat()
                if incident.created_at
                else None
            ),
            "workflow_run_id": incident.workflow_run_id,
            "failure_type": incident.failure_type,
            "root_cause": incident.root_cause,
            "fix_description": incident.fix_description,
            "outcome": incident.outcome,
            "pr_number": incident.pr_number,
            "pr_status": incident.pr_status,
            "feedback": incident.feedback,
            "target_file": incident.target_file,
            "similar_incidents": similar_incidents,
        },
    }