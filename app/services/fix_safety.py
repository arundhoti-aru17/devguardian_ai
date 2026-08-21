class FixSafetyChecker:
    """
    Validates a proposed fix before it can be applied.
    """

    MAX_DIFF_LINES = 20

    def check(self, fix) -> dict:
        """
        Check whether a proposed fix is safe to proceed with.
        """

        reasons = []

        # Rule 1: Confidence check
        if fix.confidence < 0.80:
            reasons.append(
                f"Confidence is too low: {fix.confidence}"
            )

        # Rule 2: Diff must exist
        if not fix.diff.strip():
            reasons.append("The proposed diff is empty.")

        # Rule 3: Count changed lines
        diff_lines = [
            line
            for line in fix.diff.splitlines()
            if line.startswith("+") or line.startswith("-")
        ]

        # Ignore diff header lines
        changed_lines = [
            line
            for line in diff_lines
            if not line.startswith("+++")
            and not line.startswith("---")
        ]

        if len(changed_lines) > self.MAX_DIFF_LINES:
            reasons.append(
                f"Diff changes {len(changed_lines)} lines, "
                f"which exceeds the limit of {self.MAX_DIFF_LINES}."
            )

        # Final decision
        if reasons:
            return {
                "safe": False,
                "requires_human_review": True,
                "reasons": reasons,
            }

        return {
            "safe": True,
            "requires_human_review": False,
            "reasons": [],
        }