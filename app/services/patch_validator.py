from pathlib import Path


class PatchValidator:
    """
    Validates that an AI-generated unified diff actually matches
    the current contents of the target repository file.

    The validator does NOT apply the patch.

    It checks:
    1. Removed lines exist in the current file.
    2. Context lines exist in the current file.
    3. Insertion-only patches have valid context.
    
    It supports both:
    - Proper unified diffs
    - LLM-generated diffs where the context marker space
      may be missing.
    """

    def validate(
        self,
        repo_path: str,
        file_path: str,
        diff: str,
    ) -> dict:

        # =================================================
        # 1. BASIC VALIDATION
        # =================================================

        if not repo_path:
            return {
                "valid": False,
                "reason": "Repository path is missing.",
            }

        if not file_path:
            return {
                "valid": False,
                "reason": "Target file path is missing.",
            }

        if not diff:
            return {
                "valid": False,
                "reason": "Patch diff is empty.",
            }

        # =================================================
        # 2. RESOLVE TARGET FILE
        # =================================================

        repo = Path(repo_path)
        target_file = repo / file_path

        if not target_file.exists():
            return {
                "valid": False,
                "reason": (
                    f"Target file does not exist: "
                    f"{target_file}"
                ),
            }

        if not target_file.is_file():
            return {
                "valid": False,
                "reason": (
                    f"Target path is not a file: "
                    f"{target_file}"
                ),
            }

        # =================================================
        # 3. READ CURRENT FILE
        # =================================================

        try:
            current_text = target_file.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:
            return {
                "valid": False,
                "reason": (
                    "Target file could not be decoded as UTF-8."
                ),
            }

        except OSError as exc:
            return {
                "valid": False,
                "reason": (
                    f"Unable to read target file: {exc}"
                ),
            }

        current_lines = current_text.splitlines()

        # =================================================
        # 4. PARSE DIFF
        # =================================================

        removed_lines = []
        context_lines = []
        added_lines = []

        for line in diff.splitlines():

            # ---------------------------------------------
            # Diff headers
            # ---------------------------------------------

            if line.startswith("---"):
                continue

            if line.startswith("+++"):
                continue

            # ---------------------------------------------
            # Hunk header
            # ---------------------------------------------

            if line.startswith("@@"):
                continue

            # ---------------------------------------------
            # Removed line
            # ---------------------------------------------

            if line.startswith("-"):
                removed_lines.append(
                    line[1:]
                )
                continue

            # ---------------------------------------------
            # Added line
            # ---------------------------------------------

            if line.startswith("+"):
                added_lines.append(
                    line[1:]
                )
                continue

            # ---------------------------------------------
            # Context line
            #
            # Proper unified diff:
            #
            # " " + actual file line
            #
            # But Gemini may produce:
            #
            # actual file line
            #
            # without the unified-diff marker.
            #
            # Therefore try BOTH interpretations.
            # ---------------------------------------------

            if line.startswith(" ") or line == "":

                stripped_version = (
                    line[1:]
                    if line
                    else ""
                )

                raw_version = line

                # -----------------------------------------
                # If stripping the diff marker produces a
                # real line, use that.
                # -----------------------------------------

                if stripped_version in current_lines:

                    context_lines.append(
                        stripped_version
                    )

                # -----------------------------------------
                # Otherwise check whether Gemini omitted
                # the diff marker.
                # -----------------------------------------

                elif raw_version in current_lines:

                    context_lines.append(
                        raw_version
                    )

                # -----------------------------------------
                # Neither exists.
                #
                # Keep the stripped version so the validator
                # reports the mismatch instead of silently
                # ignoring it.
                # -----------------------------------------

                else:

                    context_lines.append(
                        stripped_version
                    )

        # =================================================
        # 5. REQUIRE A REAL CHANGE
        # =================================================

        if not removed_lines and not added_lines:

            return {
                "valid": False,
                "reason": (
                    "The diff contains no additions "
                    "or removals."
                ),
            }

        # =================================================
        # 6. VALIDATE REMOVED LINES
        # =================================================

        missing_removed_lines = []

        for removed_line in removed_lines:

            if removed_line not in current_lines:

                missing_removed_lines.append(
                    removed_line
                )

        if missing_removed_lines:

            print(
                "\n❌ Removed line mismatch"
            )

            for line in missing_removed_lines:

                print(
                    f"   Missing: {repr(line)}"
                )

            return {
                "valid": False,
                "reason": (
                    "One or more lines in the patch "
                    "do not exist in the current target file."
                ),
                "missing_lines": missing_removed_lines,
            }

        # =================================================
        # 7. VALIDATE CONTEXT LINES
        # =================================================

        missing_context_lines = []

        for context_line in context_lines:

            if context_line not in current_lines:

                missing_context_lines.append(
                    context_line
                )

        if missing_context_lines:

            print(
                "\n❌ Context line mismatch"
            )

            for line in missing_context_lines:

                print(
                    f"   Missing context: {repr(line)}"
                )

            return {
                "valid": False,
                "reason": (
                    "One or more context lines in the patch "
                    "do not exist in the current target file."
                ),
                "missing_context_lines": (
                    missing_context_lines
                ),
            }

        # =================================================
        # 8. INSERTION-ONLY PATCH
        # =================================================

        if not removed_lines and added_lines:

            return {
                "valid": True,
                "reason": (
                    "Insertion-only patch is structurally "
                    "valid. All context lines exist in the "
                    "current target file."
                ),
            }

        # =================================================
        # 9. NORMAL PATCH
        # =================================================

        return {
            "valid": True,
            "reason": (
                "All removable lines and context lines "
                "exist in the current target file."
            ),
        }