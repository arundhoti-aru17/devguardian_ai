import subprocess
import json


class DockerInspector:
    """
    Inspects a Docker image and collects evidence
    about its actual state.
    """

    def inspect_image(self, image_name: str) -> dict:
        """
        Inspect Docker image metadata.
        """

        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip(),
            }

        image_data = json.loads(result.stdout)[0]

        return {
            "success": True,
            "image": image_name,
            "id": image_data.get("Id"),
            "created": image_data.get("Created"),
            "architecture": image_data.get("Architecture"),
            "os": image_data.get("Os"),
            "size": image_data.get("Size"),
            "environment": image_data.get("Config", {}).get("Env", []),
            "entrypoint": image_data.get("Config", {}).get("Entrypoint"),
            "cmd": image_data.get("Config", {}).get("Cmd"),
        }

    def inspect_python_packages(self, image_name: str) -> dict:
        """
        Inspect Python packages installed inside a Docker image.
        """

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                image_name,
                "python",
                "-m",
                "pip",
                "list",
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip(),
            }

        try:
            packages = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Could not parse pip package information.",
            }

        return {
            "success": True,
            "image": image_name,
            "packages": packages,
        }