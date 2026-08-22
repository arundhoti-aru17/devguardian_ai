def handle_issues(payload):
    issue = payload.get("issue", {})

    return {
        "event": "issues",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "number": issue.get("number", "Unknown"),
        "title": issue.get("title", "Unknown"),
        "state": issue.get("state", "Unknown"),
        "author": issue.get("user", {}).get("login", "Unknown"),
        "url": issue.get("html_url", "Unknown"),
    }