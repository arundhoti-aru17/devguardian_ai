from typing import Optional, TypedDict

from app.schemas.diagnosis import Diagnosis
from app.schemas.fix import FixRecommendation


class DevGuardianState(TypedDict):
    """
    Shared state passed between all DevGuardian agents.
    """

    # =====================================================
    # Failure information
    # =====================================================

    logs: str

    # =====================================================
    # Repository information
    # =====================================================

    repo_path: str
    repo_owner: str
    repo_name: str
    base_branch: str

    # =====================================================
    # GitHub Actions workflow run
    # =====================================================

    run_id: Optional[int]

    # =====================================================
    # M6 — Incident Connection
    # =====================================================

    incident_id: Optional[int]

    # =====================================================
    # Graph routing
    # =====================================================

    route: str

    # =====================================================
    # AI diagnosis
    # =====================================================

    diagnosis: Optional[Diagnosis]

    # =====================================================
    # M6 — Incident Memory
    # =====================================================

    memory_context: Optional[str]

    # =====================================================
    # AI-generated fix
    # =====================================================

    fix: Optional[FixRecommendation]

    # =====================================================
    # Patch validation
    # =====================================================

    patch_validation: Optional[dict]

    # =====================================================
    # Safety validation
    # =====================================================

    safety: Optional[dict]

    # =====================================================
    # GitHub remediation result
    # =====================================================

    remediation: Optional[dict]