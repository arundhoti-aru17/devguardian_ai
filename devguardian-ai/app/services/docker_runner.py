import subprocess


class DockerRunner:

    def build(self):

        result = subprocess.run(
            ["docker", "build", "-t", "docker-demo", "."],
            cwd="../devguardian-docker-demo",
            capture_output=True,
            text=True,
        )

        return result.stdout + result.stderr