from fastapi import APIRouter, Request
from app.db.session import SessionLocal
from app.db.models import Incident

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):

    payload = await request.json()
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
       "payload": payload,
    }