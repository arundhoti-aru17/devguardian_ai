def handle_pull_request(payload):
    pr = payload.get("pull_request", {})

    return {
        "event": "pull_request",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "number": pr.get("number", "Unknown"),
        "title": pr.get("title", "Unknown"),
        "state": pr.get("state", "Unknown"),
        "author": pr.get("user", {}).get("login", "Unknown"),
        "branch": pr.get("head", {}).get("ref", "Unknown"),
        "target_branch": pr.get("base", {}).get("ref", "Unknown"),
        "url": pr.get("html_url", "Unknown"),
    }