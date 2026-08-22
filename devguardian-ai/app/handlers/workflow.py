def handle_workflow(payload):
    workflow = payload.get("workflow_run", {})

    return {
        "event": "workflow_run",
        "workflow": workflow.get("name", "Unknown"),
        "status": workflow.get("status", "Unknown"),
        "conclusion": workflow.get("conclusion", "Unknown"),
        "branch": workflow.get("head_branch", "Unknown"),
    }