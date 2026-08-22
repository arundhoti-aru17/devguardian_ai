class DockerEvidenceChecker:
    """
    Compares a diagnosis with evidence collected
    from a Docker image.
    """

    def check(self, diagnosis: dict, inspection: dict) -> dict:
        """
        Confirm, refute, or mark a diagnosis as inconclusive.
        """

        if not inspection.get("success"):
            return {
                "status": "INCONCLUSIVE",
                "reason": inspection.get(
                    "error",
                    "Docker inspection failed."
                ),
                "evidence": [],
            }

        package_name = diagnosis.get("package")
        expected_version = diagnosis.get("expected_version")

        packages = inspection.get("packages", [])

        installed_packages = {
            package["name"].lower(): package["version"]
            for package in packages
        }

        # We need package + expected version to perform
        # an actual dependency comparison.
        if package_name and expected_version:

            actual_version = installed_packages.get(
                package_name.lower()
            )

            # Package is not installed inside the image.
            if actual_version is None:
                return {
                    "status": "CONFIRMED",
                    "reason": (
                        f"{package_name} is not installed in the "
                        "Docker image, but the diagnosis expects "
                        f"version {expected_version}."
                    ),
                    "evidence": [
                        f"Expected: {package_name}=={expected_version}",
                        f"Actual: {package_name} is not installed",
                    ],
                }

            # Versions are different.
            if actual_version != expected_version:
                return {
                    "status": "CONFIRMED",
                    "reason": (
                        f"{package_name} version mismatch detected."
                    ),
                    "evidence": [
                        f"Expected: {package_name}=={expected_version}",
                        f"Actual: {package_name}=={actual_version}",
                    ],
                }

            # Versions match, therefore the diagnosis is not supported.
            return {
                "status": "REFUTED",
                "reason": (
                    f"{package_name} version matches the expected version."
                ),
                "evidence": [
                    f"Expected: {package_name}=={expected_version}",
                    f"Actual: {package_name}=={actual_version}",
                ],
            }

        # We don't have enough information to compare.
        return {
            "status": "INCONCLUSIVE",
            "reason": (
                "The diagnosis does not contain enough package "
                "information for Docker evidence comparison."
            ),
            "evidence": [],
        }