import re


class RuleEngine:
    """
    Rule-based classifier for common CI/CD failures.

    If a known failure pattern is found,
    return a structured diagnosis.

    Otherwise, return Unknown Error so the
    LLM can analyze it later.
    """

    RULES = [
        {
            "pattern": r"ModuleNotFoundError|No module named",
            "failure_type": "Dependency Error",
            "recommendation": "Install the missing Python package or update requirements.txt.",
            "confidence": 0.99,
        },
        {
            "pattern": r"ImportError",
            "failure_type": "Import Error",
            "recommendation": "Check Python imports and installed packages.",
            "confidence": 0.95,
        },
        {
            "pattern": r"KeyError",
            "failure_type": "Missing Environment Variable",
            "recommendation": "Verify GitHub Secrets or environment variables.",
            "confidence": 0.95,
        },
        {
            "pattern": r"Permission denied",
            "failure_type": "Permission Error",
            "recommendation": "Check workflow permissions or file permissions.",
            "confidence": 0.90,
        },
        {
            "pattern": r"npm ERR!",
            "failure_type": "NPM Dependency Error",
            "recommendation": "Review package.json and dependency versions.",
            "confidence": 0.95,
        },
        {
            "pattern": r"FAILED|AssertionError",
            "failure_type": "Test Failure",
            "recommendation": "Inspect the failing test and expected output.",
            "confidence": 0.90,
        },
        {
            "pattern": r"Could not find a version that satisfies the requirement|No matching distribution found",
            "failure_type": "Dependency Version Mismatch",
            "recommendation": "Check the package version in requirements.txt or install a valid version.",
            "confidence": 0.99,
        },
        {
            "pattern": r"Traceback",
            "failure_type": "Python Runtime Error",
            "recommendation": "Inspect the stack trace to locate the error.",
            "confidence": 0.85,
        },
    ]

    def classify(self, logs: str) -> dict:
        """
        Search the logs for known failure patterns.
        """

        for rule in self.RULES:

            if re.search(
                rule["pattern"],
                logs,
                re.IGNORECASE,
            ):

                return {
                    "matched": True,
                    "failure_type": rule["failure_type"],
                    "recommendation": rule["recommendation"],
                    "confidence": rule["confidence"],
                }

        return {
            "matched": False,
            "failure_type": "Unknown Error",
            "recommendation": "Escalate to the LLM.",
            "confidence": 0.0,
        }