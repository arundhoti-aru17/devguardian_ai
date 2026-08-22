from pathlib import Path


class LogReader:
    """
    Reads all extracted GitHub Actions log files
    and combines them into one string.
    """

    def read_logs(self, log_directory: str) -> str:
        """
        Read every .txt file inside the extracted
        workflow logs directory.

        Returns one combined string.
        """

        log_path = Path(log_directory)

        combined_logs = ""

        # Find every .txt file recursively
        for file in sorted(log_path.rglob("*.txt")):

            print(f"Reading: {file.name}")

            combined_logs += f"\n\n========== {file.name} ==========\n"

            combined_logs += file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        return combined_logs