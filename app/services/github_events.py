from app.handlers.push import handle_push
from app.handlers.workflow import handle_workflow
from app.handlers.pull_request import handle_pull_request
from app.handlers.check_run import handle_check_run
from app.handlers.check_suite import handle_check_suite
from app.handlers.deployment import handle_deployment
from app.handlers.deployment_status import handle_deployment_status
from app.handlers.issues import handle_issues
from app.handlers.release import handle_release
from app.handlers.create import handle_create


EVENT_HANDLERS = {
    "push": handle_push,
    "workflow_run": handle_workflow,
    "pull_request": handle_pull_request,
    "check_run": handle_check_run,
    "check_suite": handle_check_suite,
    "deployment": handle_deployment,
    "deployment_status": handle_deployment_status,
    "issues": handle_issues,
    "release": handle_release,
    "create": handle_create,
}


def dispatch_event(event: str, payload: dict):
    handler = EVENT_HANDLERS.get(event)

    if handler:
        return handler(payload)

    return {
        "event": event,
        "message": f"Unsupported event: {event}",
    }