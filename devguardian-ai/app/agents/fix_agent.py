from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.schemas.diagnosis import Diagnosis
from app.schemas.fix import FixRecommendation


class FixAgent(BaseAgent):
    """
    Agent responsible for generating safe fix recommendations.

    The Fix Agent dynamically discovers the most relevant target
    file from the actual repository instead of relying on a hardcoded
    failure-type -> filename mapping.

    Flow:

        Diagnosis
            +
        GitHub Logs
            +
        Incident Memory
            +
        Repository File Inventory
            ↓
        Dynamic Target File Discovery
            ↓
        Read Actual Target File
            ↓
        Generate Minimal Patch
    """

    SUPPORTED_FAILURES = {
        "dependency",
        "version",
        "environment",
        "env",
        "flaky",
        "retry",
        "configuration",
        "config",
    }

    # =========================================================
    # REPOSITORY FILE DISCOVERY
    # =========================================================

    def _collect_repository_files(
        self,
        repo_path: str,
    ) -> list[str]:
        """
        Collect relevant text/configuration files from the
        actual repository.

        This is intentionally repository-driven.

        We do NOT assume that the repository must contain:

            requirements.txt
            pyproject.toml
            ci.yml
            Dockerfile

        Instead, we inspect what actually exists.
        """

        repo = Path(repo_path)

        if not repo.exists():
            return []

        ignored_directories = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".idea",
            ".vscode",
        }

        allowed_extensions = {
            ".py",
            ".yml",
            ".yaml",
            ".toml",
            ".txt",
            ".json",
            ".ini",
            ".cfg",
            ".conf",
            ".xml",
            ".md",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".kt",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".cs",
            ".cpp",
            ".c",
            ".h",
            ".sh",
            ".bat",
            ".ps1",
        }

        special_files = {
            "Dockerfile",
            "Makefile",
            "Jenkinsfile",
            "Procfile",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Pipfile",
            "Pipfile.lock",
            "tox.ini",
            ".env.example",
        }

        discovered = []

        try:

            for path in repo.rglob("*"):

                if not path.is_file():
                    continue

                # ---------------------------------------------
                # Ignore files inside generated / dependency
                # directories.
                # ---------------------------------------------

                relative_parts = path.relative_to(repo).parts

                if any(
                    part in ignored_directories
                    for part in relative_parts
                ):
                    continue

                # ---------------------------------------------
                # Include known special files.
                # ---------------------------------------------

                if path.name in special_files:

                    discovered.append(
                        str(
                            path.relative_to(repo)
                        ).replace("\\", "/")
                    )

                    continue

                # ---------------------------------------------
                # Include useful source/config files.
                # ---------------------------------------------

                if path.suffix.lower() in allowed_extensions:

                    discovered.append(
                        str(
                            path.relative_to(repo)
                        ).replace("\\", "/")
                    )

        except OSError as exc:

            print(
                f"⚠️ Repository file discovery failed: {exc}"
            )

            return []

        # Remove duplicates and sort.
        discovered = sorted(
            set(discovered)
        )

        return discovered

    # =========================================================
    # FILE CONTENT PREVIEW
    # =========================================================

    def _build_file_inventory(
        self,
        repo_path: str,
        files: list[str],
        max_files: int = 100,
        max_chars_per_file: int = 5000,
    ) -> str:
        """
        Build a compact repository inventory for Gemini.

        Gemini gets:

            filename
            +
            a limited preview of its contents

        This allows the model to dynamically identify the
        relevant target file.

        We deliberately limit content so that a large repository
        does not overwhelm the model.
        """

        repo = Path(repo_path)

        inventory_parts = []

        selected_files = files[:max_files]

        for file_path in selected_files:

            target = repo / file_path

            try:

                content = target.read_text(
                    encoding="utf-8",
                    errors="replace",
                )

            except Exception:

                continue

            if len(content) > max_chars_per_file:

                content = (
                    content[:max_chars_per_file]
                    + "\n...[truncated]..."
                )

            inventory_parts.append(
                f"""
--- FILE: {file_path} ---

{content}
"""
            )

        if not inventory_parts:

            return "No readable repository files were found."

        return "\n".join(
            inventory_parts
        )

    # =========================================================
    # DYNAMIC TARGET FILE DISCOVERY
    # =========================================================

    def _find_target_file(
        self,
        diagnosis: Diagnosis,
        logs: str,
        repo_path: str,
        memory_context: str | None = None,
    ) -> str:
        """
        Dynamically determine which repository file should be
        modified.

        IMPORTANT:

        There is intentionally NO mapping such as:

            dependency -> requirements.txt
            environment -> ci.yml

        Instead, Gemini receives:

            diagnosis
            logs
            previous incidents
            actual repository files

        and identifies the most relevant file.

        The selected path is then verified against the actual
        repository.
        """

        # -----------------------------------------------------
        # 1. Discover actual repository files
        # -----------------------------------------------------

        files = self._collect_repository_files(
            repo_path=repo_path,
        )

        if not files:

            print(
                "❌ No repository files available "
                "for dynamic target discovery."
            )

            return ""

        print(
            f"🔎 Dynamic discovery found "
            f"{len(files)} repository files."
        )

        # -----------------------------------------------------
        # 2. Build repository inventory
        # -----------------------------------------------------

        inventory = self._build_file_inventory(
            repo_path=repo_path,
            files=files,
        )

        # -----------------------------------------------------
        # 3. Previous incident context
        # -----------------------------------------------------

        if memory_context:

            memory = memory_context

        else:

            memory = (
                "No similar previous incidents were found."
            )

        # -----------------------------------------------------
        # 4. Ask Gemini to identify target
        # -----------------------------------------------------

        prompt = f"""
You are the Dynamic Target File Discovery Agent
for DevGuardian AI.

Your job is to identify the ONE repository file that
is most likely responsible for the CURRENT CI failure
and should be modified to fix it.

You MUST investigate the actual repository contents.

Do NOT assume standard filenames.

The repository may use:

- requirements.txt
- pyproject.toml
- setup.py
- package.json
- Dockerfile
- GitHub workflow files
- source files
- configuration files
- or completely different filenames.

==================================================
CURRENT DIAGNOSIS
==================================================

Failure type:
{diagnosis.failure_type}

Root cause:
{diagnosis.root_cause}

Likely file from diagnosis:
{diagnosis.likely_file}

Confidence:
{diagnosis.confidence}

Recommendation:
{diagnosis.recommendation}

==================================================
CURRENT GITHUB LOGS
==================================================

{logs}

==================================================
PREVIOUS INCIDENT MEMORY
==================================================

{memory}

Previous incidents are supporting evidence only.

Do NOT blindly reuse a previous incident's target file.

The CURRENT repository and CURRENT logs have priority.

==================================================
ACTUAL REPOSITORY FILES
==================================================

{inventory}

==================================================
TARGET FILE RULES
==================================================

Select exactly ONE file from the repository inventory.

The selected file MUST:

1. Exist in the actual repository.
2. Be relevant to the diagnosed failure.
3. Contain configuration/code/data that could realistically
   be responsible for the failure.
4. Be a file that can safely receive a minimal fix.
5. Be supported by evidence from the logs, diagnosis,
   or actual file contents.

Do NOT select a file merely because its name sounds relevant.

For example:

If the logs say a dependency version is invalid,
find the ACTUAL file containing that dependency.

If the logs show a missing environment variable,
find the ACTUAL configuration/workflow/source file
responsible for supplying or reading that variable.

If the logs show a Docker build failure,
inspect the ACTUAL Docker-related files.

If the logs show a test failure,
inspect the test and source/configuration files that
are actually relevant.

If no file can be selected with reasonable confidence,
return an empty file_path.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this format:

{{
    "file_path": "",
    "reason": "",
    "confidence": 0.0
}}

The file_path MUST be one of these actual files:

{json.dumps(files, indent=2)}
"""

        try:

            result = self.ask_gemini_json(
                prompt=prompt,
                model="gemini-3.5-flash-lite",
            )

        except Exception as exc:

            print(
                f"❌ Dynamic target discovery failed: {exc}"
            )

            return ""

        # -----------------------------------------------------
        # 5. Extract selected file
        # -----------------------------------------------------

        selected_file = result.get(
            "file_path",
            "",
        )

        if not isinstance(
            selected_file,
            str,
        ):

            return ""

        selected_file = (
            selected_file
            .strip()
            .replace("\\", "/")
        )

        # -----------------------------------------------------
        # 6. Validate model output against actual repository
        # -----------------------------------------------------

        if not selected_file:

            print(
                "⚠️ Dynamic discovery could not "
                "identify a safe target file."
            )

            return ""

        if selected_file not in files:

            print(
                "❌ Gemini selected a file that was "
                "not present in the repository inventory:"
            )

            print(
                f"   {selected_file}"
            )

            return ""

        # -----------------------------------------------------
        # 7. Final filesystem verification
        # -----------------------------------------------------

        target = (
            Path(repo_path)
            / selected_file
        )

        if not target.exists():

            print(
                "❌ Selected target does not exist:"
            )

            print(
                f"   {target}"
            )

            return ""

        if not target.is_file():

            print(
                "❌ Selected target is not a file:"
            )

            print(
                f"   {target}"
            )

            return ""

        print(
            "\n🎯 Dynamic Target Discovery"
        )

        print(
            f"   Selected file: {selected_file}"
        )

        print(
            f"   Reason: {result.get('reason', '')}"
        )

        print(
            f"   Confidence: "
            f"{result.get('confidence', 0.0)}"
        )

        return selected_file

    # =========================================================
    # BUILD FIX PROMPT
    # =========================================================

    def build_prompt(
        self,
        diagnosis: Diagnosis,
        file_path: str,
        file_content: str,
        logs: str,
        memory_context: str | None = None,
    ) -> str:
        """
        Build the Fix Agent prompt using:

        - current diagnosis
        - previous similar incidents
        - actual repository file
        - actual GitHub logs
        """

        if memory_context:

            memory_section = memory_context

        else:

            memory_section = (
                "No similar previous incidents were found."
            )

        return f"""
You are the Fix Recommendation Agent for DevGuardian AI.

Your job is to propose a SAFE, minimal fix for the
diagnosed GitHub Actions failure.

==================================================
CURRENT DIAGNOSIS
==================================================

Failure type:
{diagnosis.failure_type}

Root cause:
{diagnosis.root_cause}

Likely file from diagnosis:
{diagnosis.likely_file}

Confidence:
{diagnosis.confidence}

Recommendation:
{diagnosis.recommendation}

==================================================
PREVIOUS SIMILAR INCIDENTS
==================================================

{memory_section}

Use previous incidents as supporting evidence only.

Do NOT blindly copy an old fix.

The current repository and current GitHub logs
always take priority.

==================================================
DYNAMICALLY SELECTED TARGET FILE
==================================================

The target file selected by the Dynamic Target
Discovery stage is:

{file_path}

You MUST modify ONLY this file.

==================================================
ACTUAL TARGET FILE CONTENT
==================================================

{file_content}

==================================================
ACTUAL GITHUB LOGS
==================================================

{logs}

        ==================================================
        STRICT PATCH RULES
        ==================================================

        1. Modify ONLY:

           {file_path}

        2. Generate the unified diff against the EXACT
           file contents shown above.

        3. Every removed line MUST exist exactly in the
           current target file.

        4. Every added line must be part of the actual fix.

        5. NEVER replace a required modification with a
           blank-line insertion.

        6. If the diagnosed fix requires CHANGING an existing
           line, the diff MUST contain:

               - the original line
               + the corrected line

           Do NOT merely add a new line somewhere nearby.

        7. If the diagnosis says that an existing value,
           key, identifier, version, indentation, syntax
           character, or configuration entry is wrong,
           MODIFY THAT EXISTING LINE.

        8. For example, if the current file contains:

               test

           and the diagnosis says the correct syntax is:

               test:

           the patch MUST be:

               -  test
               +  test:

           It is NOT acceptable to produce an insertion that
           leaves the broken `test` line unchanged.

        9. Do NOT add blank lines unless the blank line itself
           is required to fix the diagnosed problem.

        10. The final patched file must actually resolve the
            diagnosed failure.

        11. Do NOT invent existing lines.

        12. Do NOT modify another file.

        13. Do NOT use placeholders.

        14. Keep the patch as small as possible.

        15. The fix MUST address the actual diagnosed
            failure, not merely make a syntactically valid
            change.

        16. Do NOT blindly copy a previous incident.

        17. Do NOT invent secret values.

        18. Do NOT hardcode credentials, API keys,
            passwords, or tokens.

        19. If the diagnosis does not provide enough
            evidence for a safe fix, return an empty diff.

        20. If the target file is not actually responsible
            for the failure, return an empty diff.

        21. The diff must use this exact target path:

            {file_path}

        22. Before returning the diff, mentally apply the
            patch to the supplied file content and verify:

            a. The patch applies cleanly.
            b. The original broken configuration is actually
               changed.
            c. The diagnosed error is actually corrected.
            d. No unrelated content is modified.
            e. No unnecessary blank lines or changes are added.

        23. IMPORTANT:

            A patch that merely adds content while leaving
            the diagnosed broken line unchanged is INVALID.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly:

{{
    "file_path": "{file_path}",
    "diff": "",
    "explanation": "",
    "confidence": 0.0
}}
"""

    # =========================================================
    # GENERATE FIX
    # =========================================================

    def generate_fix(
        self,
        diagnosis: Diagnosis,
        repo_path: str,
        logs: str,
        memory_context: str | None = None,
    ) -> FixRecommendation:
        """
        Generate a safe fix using dynamic target-file discovery.
        """

        # -----------------------------------------------------
        # 1. Dynamically discover target
        # -----------------------------------------------------

        file_path = self._find_target_file(
            diagnosis=diagnosis,
            logs=logs,
            repo_path=repo_path,
            memory_context=memory_context,
        )

        print(
            f"🎯 Fix Agent target file: {file_path}"
        )

        # -----------------------------------------------------
        # 2. No safe target
        # -----------------------------------------------------

        if not file_path:

            return FixRecommendation(
                file_path="",
                diff="",
                explanation=(
                    "Dynamic target-file discovery could "
                    "not identify a safe file to modify."
                ),
                confidence=0.0,
            )

        # -----------------------------------------------------
        # 3. Read ACTUAL target file
        # -----------------------------------------------------

        target_file = (
            Path(repo_path)
            / file_path
        )

        if not target_file.exists():

            return FixRecommendation(
                file_path=file_path,
                diff="",
                explanation=(
                    "The dynamically selected target file "
                    "does not exist."
                ),
                confidence=0.0,
            )

        if not target_file.is_file():

            return FixRecommendation(
                file_path=file_path,
                diff="",
                explanation=(
                    "The dynamically selected target path "
                    "is not a file."
                ),
                confidence=0.0,
            )

        try:

            file_content = target_file.read_text(
                encoding="utf-8",
            )

        except Exception as exc:

            return FixRecommendation(
                file_path=file_path,
                diff="",
                explanation=(
                    "Could not read the dynamically "
                    f"selected target file: {exc}"
                ),
                confidence=0.0,
            )

        # -----------------------------------------------------
        # 4. Build fix prompt
        # -----------------------------------------------------

        prompt = self.build_prompt(
            diagnosis=diagnosis,
            file_path=file_path,
            file_content=file_content,
            logs=logs,
            memory_context=memory_context,
        )

        # -----------------------------------------------------
        # 5. Ask Gemini for patch
        # -----------------------------------------------------

        try:

            fix_dict = self.ask_gemini_json(
                prompt=prompt,
                model="gemini-3.5-flash-lite",
            )

        except Exception as exc:

            return FixRecommendation(
                file_path=file_path,
                diff="",
                explanation=(
                    "Fix generation failed: "
                    f"{exc}"
                ),
                confidence=0.0,
            )

        # -----------------------------------------------------
        # 6. Never allow Gemini to change target path
        # -----------------------------------------------------

        fix_dict["file_path"] = file_path

        diff = fix_dict.get(
            "diff",
            "",
        )

        explanation = fix_dict.get(
            "explanation",
            "",
        )

        confidence = fix_dict.get(
            "confidence",
            0.0,
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        # -----------------------------------------------------
        # 7. Debug output
        # -----------------------------------------------------

        print(
            "\n========== GENERATED FIX =========="
        )

        print(
            f"Target file: {file_path}"
        )

        print(
            "Generated diff:"
        )

        print(
            diff
        )

        print(
            f"Confidence: {confidence}"
        )

        print(
            "===================================\n"
        )

        # -----------------------------------------------------
        # 8. Return structured recommendation
        # -----------------------------------------------------

        return FixRecommendation(
            file_path=file_path,
            diff=diff,
            explanation=explanation,
            confidence=confidence,
        )