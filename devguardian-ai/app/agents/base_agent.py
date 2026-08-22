from google import genai
import json

from app.core.config import settings
from app.schemas.diagnosis import Diagnosis


class BaseAgent:
    """
    Base class shared by all AI agents.
    """

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GOOGLE_API_KEY,
        )

    def ask_gemini(
        self,
        prompt: str,
        model: str,
    ) -> Diagnosis:
        """
        Send the prompt to Gemini and return a Diagnosis object.
        """

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )

        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "")
            response_text = response_text.replace("```", "")
            response_text = response_text.strip()

        diagnosis_dict = json.loads(response_text)

        return Diagnosis(**diagnosis_dict)

    def diagnose(self, logs: str) -> Diagnosis:
        """
        Generic diagnosis workflow shared by all agents.
        """

        # Step 1: Try Rule Engine
        rule_result = self.rule_engine.classify(logs)

        if rule_result["matched"]:

            print(self.success_message())

            return Diagnosis(
                failure_type=rule_result["failure_type"],
                root_cause=rule_result["failure_type"],
                likely_file=self.default_likely_file(),
                confidence=rule_result["confidence"],
                recommendation=rule_result["recommendation"],
            )

        # Step 2: Fall back to Gemini
        print("🤖 Falling back to Gemini...")

        prompt = self.build_prompt(logs)

        return self.ask_gemini(
            prompt=prompt,
            model=self.model_name(),
        )
    
    def ask_gemini_json(
    self,
    prompt: str,
    model: str,
) -> dict:
        """
        Send a prompt to Gemini and return the response as a dictionary.
        """

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
        )

        response_text = response.text.strip()

        if response_text.startswith("```json"): 
            response_text = response_text.replace("```json", "")
            response_text = response_text.replace("```", "")
            response_text = response_text.strip()

        return json.loads(response_text)    