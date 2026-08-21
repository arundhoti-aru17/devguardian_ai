from app.db.session import SessionLocal
from app.db.models import Incident
from app.services.github_api import GitHubAPI
from app.core.config import settings


class IncidentFeedbackService:
    """
    Tracks the outcome of DevGuardian-generated Pull Requests.

    Feedback states:

        open
            ↓
        merged → accepted
            OR
        closed → rejected
    """

    def __init__(self):
        self.github = GitHubAPI(
            settings.GITHUB_TOKEN
        )

    def update_incident_feedback(
        self,
        incident_id: int,
    ) -> dict:
        """
        Check the GitHub PR associated with an Incident
        and update the Incident with its current outcome.
        """

        db = SessionLocal()

        try:

            # -------------------------------------------------
            # Find Incident
            # -------------------------------------------------

            incident = db.get(
                Incident,
                incident_id,
            )

            if incident is None:

                return {
                    "success": False,
                    "message": (
                        f"Incident {incident_id} not found."
                    ),
                }

            # -------------------------------------------------
            # Make sure a PR exists
            # -------------------------------------------------

            if not incident.pr_number:

                return {
                    "success": False,
                    "message": (
                        f"Incident {incident_id} "
                        f"does not have a PR."
                    ),
                }

            # -------------------------------------------------
            # Repository information
            # -------------------------------------------------

            repository = (
                incident.repository
            )

            if "/" not in repository:

                return {
                    "success": False,
                    "message": (
                        "Incident repository must be "
                        "stored as owner/repository."
                    ),
                }

            owner, repo = repository.split(
                "/",
                1,
            )

            # -------------------------------------------------
            # Get current PR state from GitHub
            # -------------------------------------------------

            pr = self.github.get_pull_request(
                owner=owner,
                repo=repo,
                pr_number=incident.pr_number,
            )

            pr_state = pr.get(
                "state"
            )

            merged = pr.get(
                "merged",
                False,
            )

            # -------------------------------------------------
            # PR is merged
            # -------------------------------------------------

            if merged:

                incident.pr_status = "merged"

                incident.feedback = (
                    "accepted"
                )

                incident.outcome = (
                    "accepted"
                )

            # -------------------------------------------------
            # PR is closed but NOT merged
            # -------------------------------------------------

            elif pr_state == "closed":

                incident.pr_status = "closed"

                incident.feedback = (
                    "rejected"
                )

                incident.outcome = (
                    "rejected"
                )

            # -------------------------------------------------
            # PR is still open
            # -------------------------------------------------

            else:

                incident.pr_status = "open"

                incident.feedback = (
                    "pending"
                )

                incident.outcome = (
                    "pending"
                )

            db.commit()

            print(
                f"🧠 Incident {incident_id} "
                f"feedback updated:"
            )

            print(
                f"   PR: #{incident.pr_number}"
            )

            print(
                f"   PR status: {incident.pr_status}"
            )

            print(
                f"   Feedback: {incident.feedback}"
            )

            print(
                f"   Outcome: {incident.outcome}"
            )

            return {
                "success": True,
                "incident_id": incident.id,
                "pr_number": incident.pr_number,
                "pr_status": incident.pr_status,
                "feedback": incident.feedback,
                "outcome": incident.outcome,
            }

        except Exception as exc:

            db.rollback()

            print(
                f"❌ Failed to update Incident "
                f"{incident_id} feedback: {exc}"
            )

            return {
                "success": False,
                "incident_id": incident_id,
                "error": str(exc),
            }

        finally:

            db.close()