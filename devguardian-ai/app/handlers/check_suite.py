def handle_check_suite(payload):
    suite = payload.get("check_suite", {})

    return {
        "event": "check_suite",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "status": suite.get("status", "Unknown"),
        "conclusion": suite.get("conclusion", "Unknown"),
        "head_branch": suite.get("head_branch", "Unknown"),
        "head_sha": suite.get("head_sha", "Unknown"),
    }