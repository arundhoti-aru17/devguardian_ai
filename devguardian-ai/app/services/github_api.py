import requests


class GitHubAPI:
    """
    Client for interacting with the GitHub REST API.
    """

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    def get_authenticated_user(self):
        """
        Get the GitHub user associated with the token.
        """

        url = "https://api.github.com/user"

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # GITHUB ACTIONS
    # =========================================================

    def get_workflow_run(
        self,
        owner,
        repo,
        run_id,
    ):
        """
        Get information about a specific GitHub Actions run.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs/{run_id}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_workflow_jobs(
        self,
        owner,
        repo,
        run_id,
    ):
        """
        Get jobs belonging to a GitHub Actions workflow run.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs/{run_id}/jobs"
        )

        response = requests.get(
            url,
            headers=self.headers,
            params={
                "per_page": 100,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def list_workflow_runs(
        self,
        owner,
        repo,
    ):
        """
        List GitHub Actions workflow runs.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs"
        )

        response = requests.get(
            url,
            headers=self.headers,
            params={
                "per_page": 100,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # WORKFLOW LOGS
    # =========================================================

    def download_workflow_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ):
        """
        Download logs for a GitHub Actions workflow run.

        Strategy:

        1. Try the workflow-run log archive.
        2. If GitHub returns 404, retrieve the workflow jobs.
        3. Download logs from each individual job.
        4. Combine all job logs into one byte string.

        This makes DevGuardian more robust when the workflow
        log archive endpoint is temporarily unavailable or
        returns 404.
        """

        # =====================================================
        # 1. TRY WORKFLOW-RUN LOG ARCHIVE
        # =====================================================

        workflow_logs_url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/actions/runs/{run_id}/logs"
        )

        print(
            f"⬇️ Trying workflow log archive for run {run_id}..."
        )

        response = requests.get(
            workflow_logs_url,
            headers=self.headers,
            allow_redirects=True,
            timeout=60,
        )

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        if response.status_code == 200:

            print(
                "✅ Workflow log archive downloaded."
            )

            return response.content

        # =====================================================
        # 2. FALLBACK IF WORKFLOW LOG ARCHIVE RETURNS 404
        # =====================================================

        if response.status_code == 404:

            print(
                "⚠️ Workflow log archive returned 404."
            )

            print(
                "🔄 Falling back to individual job logs..."
            )

            jobs_data = self.get_workflow_jobs(
                owner=owner,
                repo=repo,
                run_id=run_id,
            )

            jobs = jobs_data.get(
                "jobs",
                [],
            )

            print(
                f"🔎 Found {len(jobs)} workflow job(s)."
            )

            # -------------------------------------------------
            # No jobs
            # -------------------------------------------------

            if not jobs:

                raise requests.HTTPError(
                    f"Workflow run {run_id} exists, "
                    f"but GitHub returned no jobs and "
                    f"the workflow log archive returned 404."
                )

            combined_logs = []

            # =================================================
            # 3. DOWNLOAD EACH JOB'S LOG
            # =================================================

            for job in jobs:

                job_id = job.get("id")

                job_name = job.get(
                    "name",
                    f"job-{job_id}",
                )

                job_status = job.get(
                    "status"
                )

                job_conclusion = job.get(
                    "conclusion"
                )

                print(
                    f"📄 Job: {job_name}"
                )

                print(
                    f"   ID: {job_id}"
                )

                print(
                    f"   Status: {job_status}"
                )

                print(
                    f"   Conclusion: {job_conclusion}"
                )

                if not job_id:
                    print(
                        "⚠️ Job has no ID. Skipping."
                    )
                    continue

                # -------------------------------------------------
                # Individual job logs endpoint
                # -------------------------------------------------

                job_logs_url = (
                    f"https://api.github.com/repos/"
                    f"{owner}/{repo}/actions/jobs/"
                    f"{job_id}/logs"
                )

                print(
                    f"⬇️ Downloading logs for job "
                    f"{job_name}..."
                )

                job_response = requests.get(
                    job_logs_url,
                    headers=self.headers,
                    allow_redirects=True,
                    timeout=60,
                )

                # -------------------------------------------------
                # Job log downloaded
                # -------------------------------------------------

                if job_response.status_code == 200:

                    print(
                        f"✅ Logs downloaded for job "
                        f"{job_name}."
                    )

                    combined_logs.append(
                        f"\n\n"
                        f"========== JOB: {job_name} "
                        f"==========\n\n"
                    )

                    combined_logs.append(
                        job_response.text
                    )

                else:

                    print(
                        f"⚠️ Failed to download logs for "
                        f"job {job_name}."
                    )

                    print(
                        f"   HTTP status: "
                        f"{job_response.status_code}"
                    )

            # =================================================
            # 4. CHECK WHETHER ANY LOGS WERE DOWNLOADED
            # =================================================

            if not combined_logs:

                raise requests.HTTPError(
                    f"Could not download any job logs "
                    f"for workflow run {run_id}."
                )

            print(
                "✅ Individual workflow job logs combined."
            )

            return "".join(
                combined_logs
            ).encode("utf-8")

        # =====================================================
        # 5. OTHER HTTP ERROR
        # =====================================================

        response.raise_for_status()

        return response.content

    # =========================================================
    # REPOSITORY
    # =========================================================

    def download_repository_archive(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
    ):
        """
        Download the repository as a ZIP archive
        for the specified branch.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/zipball/{branch}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            allow_redirects=True,
            timeout=60,
        )

        response.raise_for_status()

        return response.content

    # =========================================================
    # BRANCH OPERATIONS
    # =========================================================

    def get_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
    ):
        """
        Get information about a GitHub branch.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/branches/{branch}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        base_branch: str = "main",
    ):
        """
        Create a new branch from the latest commit
        of the base branch.
        """

        base = self.get_branch(
            owner=owner,
            repo=repo,
            branch=base_branch,
        )

        base_sha = base["commit"]["sha"]

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/git/refs"
        )

        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # FILE OPERATIONS
    # =========================================================

    def get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: str = "main",
    ):
        """
        Get a file from a GitHub repository.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/contents/{path}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            params={
                "ref": branch,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        file_sha: str,
        branch: str,
        commit_message: str,
    ):
        """
        Update a file on a GitHub branch.
        """

        import base64

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/contents/{path}"
        )

        encoded_content = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": commit_message,
            "content": encoded_content,
            "sha": file_sha,
            "branch": branch,
        }

        response = requests.put(
            url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # PULL REQUEST OPERATIONS
    # =========================================================

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ):
        """
        Create a Pull Request on GitHub.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/pulls"
        )

        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ):
        """
        Get the current state of a Pull Request.

        GitHub returns:
            state   -> open / closed
            merged  -> true / false
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/pulls/{pr_number}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # =========================================================
    # LABEL OPERATIONS
    # =========================================================

    def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: str,
    ):
        """
        Create a label in a GitHub repository.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/labels"
        )

        payload = {
            "name": name,
            "color": color,
            "description": description,
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 422:
            return {
                "created": False,
                "message": "Label already exists.",
            }

        response.raise_for_status()

        return response.json()

    def add_labels_to_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        labels: list[str],
    ):
        """
        Add labels to a Pull Request.
        """

        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/issues/"
            f"{pr_number}/labels"
        )

        payload = {
            "labels": labels,
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()