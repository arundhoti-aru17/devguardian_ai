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
        """

        # -----------------------------------------------------
        # Generate embedding for the current incident
        # -----------------------------------------------------

        query_embedding = (
            self.generate_incident_embedding(
                incident
            )
        )

        # -----------------------------------------------------
        # Calculate cosine distance
        #
        # Smaller distance = more similar
        # -----------------------------------------------------

        distance = Incident.embedding.cosine_distance(
            query_embedding
        )

        # -----------------------------------------------------
        # Search PostgreSQL
        #
        # Exclude the current incident itself.
        # Ignore incidents without embeddings.
        # Ignore incidents that are too different.
        # -----------------------------------------------------

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