from fastapi import APIRouter, Request, Header
from app.db.session import SessionLocal
from app.db.models import Incident
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default="Unknown"),
):

    # Read the JSON payload sent by GitHub
    payload = await request.json()
    if x_github_event == "push":
        print("🚀 ENTERED PUSH BLOCK")
        repository = payload.get("repository", {}).get("name", "Unknown")
        branch = payload.get("ref", "Unknown")
        pusher = payload.get("pusher", {}).get("name", "Unknown")

        commits = payload.get("commits", [])

        if commits:
            latest_commit = commits[-1]
            commit_message = latest_commit.get("message", "Unknown")
        else:
            commit_message = "No commits"

        print(f"Repository: {repository}")
        print(f"Branch: {branch}")
        print(f"Pusher: {pusher}")
        print(f"Latest Commit: {commit_message}")
        
        
        print("📌 Push Event Received")

    elif x_github_event == "workflow_run":
        print("⚙️ Workflow Event Received")

    elif x_github_event == "pull_request":
        print("🔀 Pull Request Event Received")

    else:
        print(f"❓ Unsupported Event: {x_github_event}")

    # Print the event type and payload
    print("=" * 60)
    print(f"GitHub Event: {x_github_event}")
    print(payload)
    print("=" * 60)

    repository = payload.get("repository", {}).get("name", "Unknown")
    branch = payload.get("ref", "Unknown")
    workflow = payload.get("workflow_run", {}).get("name", "Unknown")
    status = payload.get("action", "Unknown")

    db = SessionLocal()

    try:
        incident = Incident(
            repository=repository,
            branch=branch,
            workflow=workflow,
            status=status,
        )

        db.add(incident)
        db.commit()
        print("✅ Commit Successful")

        db.refresh(incident)

    except Exception as e:
        print("❌ Commit Failed:", e)
        raise

    finally:
        db.close()

    return {
        "message": "GitHub Webhook Received",
        "event": x_github_event,
    }