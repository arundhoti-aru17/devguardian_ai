from app.schemas.diagnosis import Diagnosis
from app.services.kubernetes_rule_engine import KubernetesRuleEngine
from app.agents.base_agent import BaseAgent


class KubernetesAgent(BaseAgent):
    """
    Agent responsible for diagnosing Kubernetes failures.
    """

    def __init__(self):

        super().__init__()

        self.rule_engine = KubernetesRuleEngine()

    def diagnose(self, logs: str) -> Diagnosis:
        """
        Diagnose Kubernetes failures.
        """

        # Step 1: Try the Rule Engine first
        rule_result = self.rule_engine.classify(logs)

        if rule_result["matched"]:

            print("✅ Kubernetes Rule Engine handled the diagnosis.")

            return Diagnosis(
                failure_type=rule_result["failure_type"],
                root_cause=rule_result["failure_type"],
                likely_file="Kubernetes configuration",
                confidence=rule_result["confidence"],
                recommendation=rule_result["recommendation"],
            )

        # Step 2: Rule Engine doesn't recognize it
        print("🤖 Falling back to Gemini...")

        prompt = f"""
You are an expert Kubernetes and DevOps Engineer.

Analyze the following Kubernetes logs.

Identify the failure and explain its likely root cause.

Return ONLY valid JSON.

{{
    "failure_type": "",
    "root_cause": "",
    "likely_file": "",
    "confidence": 0.0,
    "recommendation": ""
}}

Kubernetes logs:

{logs}
"""

        return self.ask_gemini(
            prompt=prompt,
            model="gemini-3.5-flash-lite",
        )