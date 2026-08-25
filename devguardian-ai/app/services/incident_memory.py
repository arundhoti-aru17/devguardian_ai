from sqlalchemy.orm import Session

from app.db.models import Incident
from app.services.embedding_service import EmbeddingService


class IncidentMemory:
    """
    Stores incident embeddings and retrieves similar incidents.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()

    # =========================================================
    # BUILD EMBEDDING TEXT
    # =========================================================

    def build_embedding_text(
        self,
        incident: Incident,
    ) -> str:
        """
        Build the text representation that will be embedded.
        """

        return f"""
Failure type: {incident.failure_type or ""}
Root cause: {incident.root_cause or ""}
Fix description: {incident.fix_description or ""}
Outcome: {incident.outcome or ""}
Repository: {incident.repository or ""}
Workflow: {incident.workflow or ""}
""".strip()

    # =========================================================
    # GENERATE EMBEDDING
    # =========================================================

    def generate_incident_embedding(
        self,
        incident: Incident,
    ) -> list[float]:
        """
        Generate a 384-dimensional embedding for an incident.
        """

        text = self.build_embedding_text(
            incident
        )

        return self.embedding_service.generate_embedding(
            text
        )

    # =========================================================
    # STORE EMBEDDING
    # =========================================================

    def store_embedding(
        self,
        db: Session,
        incident: Incident,
    ) -> Incident:
        """
        Generate and store the embedding for an incident.
        """

        embedding = self.generate_incident_embedding(
            incident
        )

        incident.embedding = embedding

        db.add(incident)

        db.commit()

        db.refresh(incident)

        return incident

    # =========================================================
    # FIND SIMILAR INCIDENTS
    # =========================================================

    def find_similar_incidents(
        self,
        db: Session,
        incident: Incident,
        limit: int = 5,
        similarity_threshold: float = 0.30,
    ) -> list[Incident]:
        """
        Find previous incidents that are semantically similar
        to the supplied incident.

        PostgreSQL + pgvector uses cosine distance.

        Smaller cosine distance = more similar.

        Only incidents whose cosine distance is less than or
        equal to similarity_threshold are considered similar.

        Kept for backwards compatibility. Prefer
        find_similar_incidents_with_scores when the caller needs
        to display *how* similar a match is (e.g. in the API
        response), since this method discards the distance value.
        """

        query_embedding = (
            self.generate_incident_embedding(
                incident
            )
        )

        distance = Incident.embedding.cosine_distance(
            query_embedding
        )

        similar_incidents = (
            db.query(Incident)
            .filter(
                Incident.id != incident.id,
                Incident.embedding.isnot(None),
                distance <= similarity_threshold,
            )
            .order_by(distance)
            .limit(limit)
            .all()
        )

        return similar_incidents

    # =========================================================
    # FIND SIMILAR INCIDENTS (WITH SIMILARITY SCORES)
    # =========================================================

    def find_similar_incidents_with_scores(
        self,
        db: Session,
        incident: Incident,
        limit: int = 5,
        similarity_threshold: float = 0.30,
    ) -> list[tuple[Incident, float]]:
        """
        Same matching logic as find_similar_incidents, but also
        returns a 0-1 similarity score per match (1 = identical,
        0 = completely dissimilar), so API responses can surface
        "how confident" a memory match is instead of just which
        incidents matched.

        cosine_distance ranges roughly 0 (identical) to 2
        (opposite). We convert it to a similarity score via
        `1 - distance`, which is the standard cosine-similarity
        relationship and stays intuitive (higher = more similar).
        """

        query_embedding = (
            self.generate_incident_embedding(
                incident
            )
        )

        distance = Incident.embedding.cosine_distance(
            query_embedding
        )

        rows = (
            db.query(Incident, distance.label("distance"))
            .filter(
                Incident.id != incident.id,
                Incident.embedding.isnot(None),
                distance <= similarity_threshold,
            )
            .order_by(distance)
            .limit(limit)
            .all()
        )

        return [
            (matched_incident, round(1 - matched_distance, 4))
            for matched_incident, matched_distance in rows
        ]