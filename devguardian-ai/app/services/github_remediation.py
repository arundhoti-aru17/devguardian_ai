from app.services.github_api import GitHubAPI
from app.services.patch_applier import PatchApplier
from app.services.fix_safety import FixSafetyChecker


class GitHubRemediation:
    """
    Coordinates the complete GitHub remediation workflow.

    Flow:

    Fix
      ↓
    Safety Check
      ↓
    Create Branch
      ↓
    Get File
      ↓
    Apply Patch
      ↓
    Update File
      ↓
    Create PR
      ↓
    Add Label
    """

    def __init__(self, github: GitHubAPI):
        self.github = github
        self.patch_applier = PatchApplier()
        self.safety_checker = FixSafetyChecker()

    def remediate(
        self,
        owner: str,
        repo: str,
        fix,
        base_branch: str = "main",
        branch_name: str = "devguardian/auto-fix",
    ) -> dict:
        """
        Execute the complete GitHub remediation workflow.

        Important:
        GitHub API paths always use forward slashes.
        """

        # =====================================================
        # NORMALIZE FILE PATH
        # =====================================================

        github_file_path = fix.file_path.replace("\\", "/")

        print(
            f"📄 Remediation target: {github_file_path}"
        )

        # =====================================================
        # 1. SAFETY CHECK
        # =====================================================

        safety = self.safety_checker.check(fix)

        if not safety["safe"]:
            return {
                "success": False,
                "stage": "safety_check",
                "safety": safety,
                "message": "Fix rejected by safety checker.",
            }

        # =====================================================
        # 2. CREATE BRANCH
        # =====================================================

        print(
            f"🌿 Creating remediation branch: {branch_name}"
        )

        try:

            branch_result = self.github.create_branch(
                owner=owner,
                repo=repo,
                branch_name=branch_name,
                base_branch=base_branch,
            )

            print(
                "✅ Remediation branch created."
            )

        except Exception as exc:

            # -------------------------------------------------
            # The branch may already exist.
            #
            # This can happen when LangGraph retries the
            # complete remediation after the branch was already
            # created during a previous attempt.
            # -------------------------------------------------

            error_text = str(exc)

            if (
                "422" in error_text
                or "Reference already exists" in error_text
                or "already exists" in error_text
            ):

                print(
                    "ℹ️ Remediation branch already exists."
                )

            else:

                raise

        # =====================================================
        # 3. GET TARGET FILE
        # =====================================================

        print(
            f"📄 Getting file from GitHub: "
            f"{github_file_path}"
        )

        file_data = self.github.get_file(
            owner=owner,
            repo=repo,
            path=github_file_path,
            branch=branch_name,
        )

        # =====================================================
        # 4. APPLY PATCH LOCALLY
        # =====================================================

        import base64
        import tempfile
        from pathlib import Path

        current_content = base64.b64decode(
            file_data["content"]
        ).decode("utf-8")

        with tempfile.TemporaryDirectory() as temp_dir:

            # -------------------------------------------------
            # Use POSIX-style path for consistency.
            # pathlib on Windows will still handle it correctly.
            # -------------------------------------------------

            target_file = (
                Path(temp_dir)
                / github_file_path
            )

            target_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target_file.write_text(
                current_content,
                encoding="utf-8",
            )

            print(
                "🩹 Applying DevGuardian patch..."
            )

            patch_result = self.patch_applier.apply(
                repo_path=temp_dir,
                file_path=github_file_path,
                diff=fix.diff,
            )

            if not patch_result["success"]:

                return {
                    "success": False,
                    "stage": "patch_application",
                    "error": patch_result["error"],
                }

            new_content = target_file.read_text(
                encoding="utf-8"
            )

        print(
            "✅ Patch applied successfully."
        )

        # =====================================================
        # 5. UPDATE FILE ON GITHUB
        # =====================================================

        print(
            "⬆️ Updating file on GitHub..."
        )

        update_result = self.github.update_file(
            owner=owner,
            repo=repo,
            path=github_file_path,
            content=new_content,
            file_sha=file_data["sha"],
            branch=branch_name,
            commit_message=(
                "fix: apply DevGuardian recommendation "
                f"to {github_file_path}"
            ),
        )

        print(
            "✅ File updated on GitHub."
        )

        # =====================================================
        # 6. CREATE PULL REQUEST
        # =====================================================

        print(
            "🔀 Creating Pull Request..."
        )

        pr_result = self.github.create_pull_request(
            owner=owner,
            repo=repo,
            title="🤖 DevGuardian automated fix",
            body=self._build_pr_body(
                fix=fix,
                file_path=github_file_path,
            ),
            head=branch_name,
            base=base_branch,
        )

        print(
            f"✅ Pull Request created: "
            f"#{pr_result['number']}"
        )

        # =====================================================
        # 7. ADD DEVGUARDIAN LABEL
        # =====================================================

        try:

            self.github.add_labels_to_pr(
                owner=owner,
                repo=repo,
                pr_number=pr_result["number"],
                labels=[
                    "devguardian-fix",
                ],
            )

            print(
                "🏷️ DevGuardian label added."
            )

        except Exception as exc:

            # -------------------------------------------------
            # Label failure should not make the entire
            # remediation fail after the PR already exists.
            # -------------------------------------------------

            print(
                f"⚠️ Could not add DevGuardian label: {exc}"
            )

        # =====================================================
        # 8. RETURN COMPLETE RESULT
        # =====================================================

        return {
            "success": True,
            "stage": "completed",
            "branch": branch_name,
            "commit_sha": update_result["commit"]["sha"],
            "pr_number": pr_result["number"],
            "pr_url": pr_result["html_url"],
            "safety": safety,
        }

    def _build_pr_body(
        self,
        fix,
        file_path: str,
    ) -> str:
        """
        Build the Pull Request description.
        """

        return f"""## 🤖 DevGuardian AI Fix

### File

`{file_path}`

### Explanation

{fix.explanation}

### Proposed Change

```diff
{fix.diff}
```
"""