import requests


class GitHubAPI:

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

    def get_authenticated_user(self):
        url = "https://api.github.com/user"

        response = requests.get(
            url,
            headers=self.headers,
        )

        response.raise_for_status()

        return response.json()

    def get_workflow_run(self, owner, repo, run_id):
        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs/{run_id}"
        )

        response = requests.get(
            url,
            headers=self.headers,
        )

        response.raise_for_status()

        return response.json()

    def get_workflow_jobs(self, owner, repo, run_id):
        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs/{run_id}/jobs"
        )

        response = requests.get(
            url,
            headers=self.headers,
        )

        response.raise_for_status()

        return response.json()
    
    def list_workflow_runs(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

        response = requests.get(
            url,
            headers=self.headers,
        )

        response.raise_for_status()

        return response.json()  