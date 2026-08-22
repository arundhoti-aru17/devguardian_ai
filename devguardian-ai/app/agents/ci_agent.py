from app.agents.base_agent import BaseAgent
from app.services.rule_engine import RuleEngine


class CIAgent(BaseAgent):
    """
    AI Agent responsible for diagnosing
    GitHub Actions failures.
    """

    def __init__(self):
        super().__init__()
        self.rule_engine = RuleEngine()

    def build_prompt(self, logs: str) -> str:
        return f"""
You are an expert DevOps Engineer.

Analyze these GitHub Actions logs.

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
        return "gemini-3.5-flash-lite"

    def success_message(self) -> str:
        return "✅ Rule Engine handled the diagnosis."

    def default_likely_file(self) -> str:
        return "Unknown"