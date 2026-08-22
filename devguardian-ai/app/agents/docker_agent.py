from app.agents.base_agent import BaseAgent
from app.services.docker_rule_engine import DockerRuleEngine


class DockerAgent(BaseAgent):
    """
    AI Agent responsible for diagnosing Docker build failures.
    """

    def __init__(self):
        super().__init__()
        self.rule_engine = DockerRuleEngine()

    def build_prompt(self, logs: str) -> str:
        return f"""
You are an expert Docker Engineer.

Analyze these Docker build logs.

Return ONLY valid JSON.

{{
    "failure_type": "",
    "root_cause": "",
    "likely_file": "",
    "confidence": 0.0,
    "recommendation": ""
}}

Logs:

{logs}
"""

    def model_name(self) -> str:
        return "gemini-2.5-flash"

    def success_message(self) -> str:
        return "✅ Docker Rule Engine handled the diagnosis."

    def default_likely_file(self) -> str:
        return "Dockerfile"