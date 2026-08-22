import re


class DockerRuleEngine:
    """
    Rule-based classifier for common Docker build failures.
    """

    RULES = [
        {
            "pattern": r"requirements.*not found",
            "failure_type": "Missing Requirements File",
            "recommendation": "Verify that requirements.txt exists and that the COPY instruction references the correct filename.",
            "confidence": 0.99,
        },
        {
            "pattern": r"COPY failed|failed to compute cache key",
            "failure_type": "Docker COPY Error",
            "recommendation": "Verify the source file exists and the COPY path is correct.",
            "confidence": 0.99,
        },
        {
            "pattern": r"No such file or directory",
            "failure_type": "Missing File",
            "recommendation": "Check the file path referenced in the Dockerfile.",
            "confidence": 0.95,
        },
        {
            "pattern": r"failed to resolve source metadata",
            "failure_type": "Invalid Base Image",
            "recommendation": "Verify the image name and tag used in the FROM instruction.",
            "confidence": 0.99,
        },
        {
            "pattern": r"pull access denied",
            "failure_type": "Image Not Found",
            "recommendation": "Verify the base image name and registry permissions.",
            "confidence": 0.95,
        },
        {
            "pattern": r"permission denied",
            "failure_type": "Permission Error",
            "recommendation": "Check file permissions or Docker daemon permissions.",
            "confidence": 0.90,
        },
        {
            "pattern": r"Could not find a version that satisfies the requirement|No matching distribution found",
            "failure_type": "Package Installation Error",
            "recommendation": "Check the package name or version in the RUN pip install command.",
            "confidence": 0.99,
        },
        {
            "pattern": r"failed to solve",
            "failure_type": "Docker Build Failure",
            "recommendation": "Inspect the Docker build logs for the failing instruction.",
            "confidence": 0.85,
        },
    ]

    def classify(self, logs: str) -> dict:

        for rule in self.RULES:

            if re.search(rule["pattern"], logs, re.IGNORECASE):

                return {
                    "matched": True,
                    "failure_type": rule["failure_type"],
                    "recommendation": rule["recommendation"],
                    "confidence": rule["confidence"],
                }

        return {
            "matched": False,
            "failure_type": "Unknown Docker Error",
            "recommendation": "Escalate to the LLM.",
            "confidence": 0.0,
        }