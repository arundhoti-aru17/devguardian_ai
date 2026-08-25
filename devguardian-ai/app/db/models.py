from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class Incident(Base):
    """
    Stores CI/CD failures detected by DevGuardian AI.

    M6 adds incident-memory fields and a vector embedding
    so previous incidents can be retrieved using similarity search.

    M7 adds target_file so the UI can show which file DevGuardian's
    fix actually touched, instead of guessing.
    """

    __tablename__ = "incidents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    repository = Column(
        String,
        nullable=False,
    )

    branch = Column(
        String,
        nullable=False,
    )

    workflow = Column(
        String,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # =========================================================
    # GitHub Workflow Run Identity
    # =========================================================

    workflow_run_id = Column(
        BigInteger,
        nullable=True,
        index=True,
    )

    # =========================================================
    # M6 — Incident Memory
    # =========================================================

    failure_type = Column(
        String,
        nullable=True,
    )

    root_cause = Column(
        Text,
        nullable=True,
    )

    fix_description = Column(
        Text,
        nullable=True,
    )

    outcome = Column(
        String,
        nullable=True,
    )

    # =========================================================
    # M6 — Vector Embedding
    # =========================================================

    embedding = Column(
        Vector(384),
        nullable=True,
    )

    # =========================================================
    # M6 — PR Feedback
    # =========================================================

    pr_number = Column(
        Integer,
        nullable=True,
    )

    pr_status = Column(
        String,
        nullable=True,
    )

    feedback = Column(
        String,
        nullable=True,
    )

    # =========================================================
    # M7 — Fix Target
    # =========================================================

    target_file = Column(
        String,
        nullable=True,
    )