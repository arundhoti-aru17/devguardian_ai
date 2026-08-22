from pathlib import Path


class PatchApplier:
    """
    Applies a simple unified diff to a file in a target repository.
    """

    def apply(
        self,
        repo_path: str,
        file_path: str,
        diff: str,
    ) -> dict:
        """
        Apply a proposed diff to a file inside the target repository.
        """

        target_file = Path(repo_path) / file_path

        if not target_file.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        original_content = target_file.read_text(
            encoding="utf-8"
        )

        lines = original_content.splitlines()

        additions = []
        removals = []

        for line in diff.splitlines():

            # Ignore unified diff metadata
            if line.startswith("---"):
                continue

            if line.startswith("+++"):
                continue

            if line.startswith("@@"):
                continue

            if line.startswith("-"):
                removals.append(line[1:])

            elif line.startswith("+"):
                additions.append(line[1:])

        # Remove lines requested by the diff
        for line in removals:
            if line in lines:
                lines.remove(line)

        # Add new lines
        lines.extend(additions)

        new_content = "\n".join(lines) + "\n"

        target_file.write_text(
            new_content,
            encoding="utf-8",
        )

        return {
            "success": True,
            "file": file_path,
            "message": "Patch applied successfully.",
        }