class KubernetesRuleEngine:
    """
    Rule-based classifier for Kubernetes failures.
    """

    def classify(self, logs: str):

        logs_lower = logs.lower()

        # Rule 1: Kubernetes cannot pull the container image
        if (
            "imagepullbackoff" in logs_lower
            or "errimagepull" in logs_lower
            or "failed to pull image" in logs_lower
        ):
            return {
                "matched": True,
                "failure_type": "Image Pull Error",
                "confidence": 0.99,
                "recommendation": (
                    "Verify that the container image exists, "
                    "the image name and tag are correct, and "
                    "the Kubernetes node can access the image."
                ),
            }

        # Rule 2: Container keeps crashing
        if "crashloopbackoff" in logs_lower:
            return {
                "matched": True,
                "failure_type": "Container Crash",
                "confidence": 0.99,
                "recommendation": (
                    "Inspect the container logs and Pod events "
                    "to determine why the application is repeatedly crashing."
                ),
            }

        # Rule 3: Pod is stuck in Pending state
        if "pending" in logs_lower:
            return {
                "matched": True,
                "failure_type": "Pod Pending",
                "confidence": 0.95,
                "recommendation": (
                    "Inspect the Pod events and scheduling information "
                    "to determine why the Pod cannot start."
                ),
            }

        # No known Kubernetes failure detected
        return {
            "matched": False,
            "failure_type": None,
            "confidence": 0.0,
            "recommendation": None,
        }