from app.agents.ci_agent import CIAgent
from app.agents.docker_agent import DockerAgent


class AgentRouter:

    def __init__(self):

        self.ci_agent = CIAgent()

        self.docker_agent = DockerAgent()

    def route(self, logs):

        # Detect Docker logs
        if (
            "Dockerfile" in logs
            or "failed to solve" in logs
            or "docker build" in logs
        ):

            print("📦 Routing to Docker Agent")

            return self.docker_agent.diagnose(logs)

        # Detect GitHub Actions logs
        elif (
            "GitHub Actions" in logs
            or "Run pytest" in logs
            or "actions/checkout" in logs
        ):

            print("⚙️ Routing to CI Agent")

            return self.ci_agent.diagnose(logs)

        else:

            raise ValueError("Could not determine log type.")