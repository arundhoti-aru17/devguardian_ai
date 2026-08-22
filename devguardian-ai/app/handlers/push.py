def handle_push(payload):
    repository = payload.get("repository", {}).get("name", "Unknown")
    branch = payload.get("ref", "Unknown")
    pusher = payload.get("pusher", {}).get("name", "Unknown")

    commits = payload.get("commits", [])

    if commits:
        latest_commit = commits[-1]
        commit_message = latest_commit.get("message", "Unknown")
    else:
        commit_message = "No commits"

    return {
        "event": "push",
        "repository": repository,
        "branch": branch,
        "pusher": pusher,
        "commit_message": commit_message,
    }