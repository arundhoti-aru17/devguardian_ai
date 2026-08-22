from pydantic import BaseModel


class Diagnosis(BaseModel):
    """
    Standard diagnosis returned by the CI Agent.
    """

    failure_type: str

    root_cause: str

    likely_file: str

    confidence: float

    recommendation: str