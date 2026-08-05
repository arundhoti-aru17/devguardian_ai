def handle_check_run(payload):
    check_run = payload.get("check_run", {})

    return {
        "event": "check_run",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "name": check_run.get("name", "Unknown"),
        "status": check_run.get("status", "Unknown"),
        "conclusion": check_run.get("conclusion", "Unknown"),
        "head_sha": check_run.get("head_sha", "Unknown"),
        "url": check_run.get("html_url", "Unknown"),
    }