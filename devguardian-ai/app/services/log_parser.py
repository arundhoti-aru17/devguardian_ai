import re


class LogParser:
    """
    Cleans GitHub Actions logs by removing
    timestamps and common GitHub runner noise.
    """

    IGNORE_PREFIXES = (
        "##[group]",
        "##[endgroup]",
        "[command]",
        "hint:",
    )

    IGNORE_CONTAINS = (
        "Hosted Compute Agent",
        "Current runner version",
        "Worker ID",
        "Azure Region",
        "Runner Image",
        "Operating System",
        "Prepare workflow directory",
        "Prepare all required actions",
        "Getting action download info",
        "Working directory is",
        "Setting up auth",
        "Fetching the repository",
        "Disabling automatic garbage collection",
        "Syncing repository",
        "Initialized empty Git repository",
        "Temporarily overriding HOME",
        "Adding repository directory",
        "git version",
        "Job defined at",
        "Requested labels",
        "Waiting for a runner",
        "Evaluating",
        "Result:",
        "Job is about to start",
        "Job is waiting",
        "Image Release:",
        "Included Software:",
        "Contents:",
        "Metadata:",
        "Packages:",
        "Secret source:",
        "Download action repository",
        "Node 20 is being deprecated",
        "http.https://github.com/.extraheader",
        "Cleaning up orphan processes",
        "Post job cleanup.",
    )

    def clean(self, logs: str) -> str:

        cleaned = []

        for line in logs.splitlines():

            # Remove timestamp at the beginning of the line
            line = re.sub(r"^\S+\s+", "", line)

            line = line.strip()

            if not line:
                continue

            # Remove GitHub group markers but keep the useful text
            if line.startswith("##[group]"):
                line = line.replace("##[group]", "").strip()

            if line.startswith("##[endgroup]"):
                continue

            # Ignore unwanted prefixes
            if line.startswith(("[command]", "hint:")):
                continue

            # Ignore common GitHub runner noise
            if any(text in line for text in self.IGNORE_CONTAINS):
                continue

            cleaned.append(line)

        return "\n".join(cleaned)