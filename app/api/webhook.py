from fastapi import APIRouter, Request, Header
from app.db.session import SessionLocal
from app.db.models import Incident
from app.services.github_events import dispatch_event

router = APIRouter()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default="Unknown"),
):
    # Read the JSON payload sent by GitHub
    payload = await request.json()

    # Send the event to the appropriate handler
    event_data = dispatch_event(
        event=x_github_event,
        payload=payload,
    )

    print(event_data)

    # Extract fields required for database storage
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