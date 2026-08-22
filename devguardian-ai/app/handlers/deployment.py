def handle_deployment(payload):
    deployment = payload.get("deployment", {})

    return {
        "event": "deployment",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "environment": deployment.get("environment", "Unknown"),
        "ref": deployment.get("ref", "Unknown"),
        "sha": deployment.get("sha", "Unknown"),
        "creator": deployment.get("creator", {}).get("login", "Unknown"),
    }