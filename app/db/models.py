from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class Incident(Base):
    """
    Stores CI/CD failures detected by DevGuardian AI.
    """

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    repository = Column(String, nullable=False)

    branch = Column(String, nullable=False)

    workflow = Column(String, nullable=False)

    status = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )