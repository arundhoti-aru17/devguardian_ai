from google import genai
from google.genai import types
from app.core.config import settings


class EmbeddingService:
    """
    Generates vector embeddings for DevGuardian incidents.

    NOTE: text-embedding-004 was deprecated by Google on
    January 14, 2026. gemini-embedding-001 is its replacement —
    it defaults to 3072-dim output but supports truncation via
    output_dimensionality (Matryoshka Representation Learning),
    which is why we can still ask for 384 dims here and keep
    the existing pgvector(384) column unchanged.
    """

    EMBEDDING_MODEL = "gemini-embedding-001"
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