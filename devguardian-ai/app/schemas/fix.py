from pydantic import BaseModel


class FixRecommendation(BaseModel):
    """
    Structured recommendation for fixing a diagnosed failure.
    """

    file_path: str
    diff: str
    explanation: str
    confidence: float