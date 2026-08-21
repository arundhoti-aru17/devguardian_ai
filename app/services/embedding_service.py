from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Generates vector embeddings for DevGuardian incidents.
    """

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Convert text into a 384-dimensional embedding.
        """

        if not text or not text.strip():
            raise ValueError("Cannot generate embedding from empty text.")

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()