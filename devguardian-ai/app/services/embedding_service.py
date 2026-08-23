from google import genai
from google.genai import types
from app.core.config import settings


class EmbeddingService:
    """
    Generates vector embeddings for DevGuardian incidents.
    """

    EMBEDDING_MODEL = "text-embedding-004"
    EMBEDDING_DIM = 384

    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Convert text into a 384-dimensional embedding.
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding from empty text.")

        result = self.client.models.embed_content(
            model=self.EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.EMBEDDING_DIM,
            ),
        )

        return result.embeddings[0].values
