def handle_deployment_status(payload):
    status = payload.get("deployment_status", {})

    return {
        "event": "deployment_status",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "state": status.get("state", "Unknown"),
        "environment": status.get("environment", "Unknown"),
        "description": status.get("description", "Unknown"),
        "url": status.get("target_url", "Unknown"),
    }