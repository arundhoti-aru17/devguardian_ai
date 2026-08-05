from app.core.config import settings
from app.services.github_api import GitHubAPI

github = GitHubAPI(settings.GITHUB_TOKEN)

runs = github.list_workflow_runs(
    settings.GITHUB_OWNER,
    "devguardian_ai",
)

workflow_runs = runs["workflow_runs"]

print(f"Total Runs: {len(workflow_runs)}")

latest_run = workflow_runs[0]

print("Run ID:", latest_run["id"])
print("Workflow:", latest_run["name"])
print("Status:", latest_run["status"])
print("Conclusion:", latest_run["conclusion"])