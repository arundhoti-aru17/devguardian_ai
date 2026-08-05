def handle_create(payload):
    return {
        "event": "create",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "ref": payload.get("ref", "Unknown"),
        "ref_type": payload.get("ref_type", "Unknown"),
        "master_branch": payload.get("master_branch", "Unknown"),
        "description": payload.get("description", "Unknown"),
    }