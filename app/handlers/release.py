def handle_release(payload):
    release = payload.get("release", {})

    return {
        "event": "release",
        "repository": payload.get("repository", {}).get("name", "Unknown"),
        "name": release.get("name", "Unknown"),
        "tag": release.get("tag_name", "Unknown"),
        "author": release.get("author", {}).get("login", "Unknown"),
        "published_at": release.get("published_at", "Unknown"),
        "url": release.get("html_url", "Unknown"),
    }