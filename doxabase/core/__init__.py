"""doxabase.core: the DoxaBase capsule, composed from subsystem mixins.

Split from a single 74k-line module by the distillation program (Phase 2,
zero behavior change). Every public and private name that used to live at
``doxabase.core`` is re-exported here.
"""

from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403
from doxabase.core.storage import StorageMixin
from doxabase.core.search import SearchMixin
from doxabase.core.entities import EntitiesMixin
from doxabase.core.datasets import DatasetsMixin
from doxabase.core.slices import SlicesMixin
from doxabase.core.brief import BriefMixin
from doxabase.core.observations import ObservationsMixin
from doxabase.core.map_authoring import MapAuthoringMixin
from doxabase.core.profiles import ProfilesMixin
from doxabase.core.profile_records import ProfileRecordsMixin
from doxabase.core.profile_review import ProfileReviewMixin
from doxabase.core.profile_promotion import ProfilePromotionMixin
from doxabase.core.profile_advisories import ProfileAdvisoriesMixin
from doxabase.core.map_staging import MapStagingMixin
from doxabase.core.analysis_views import AnalysisViewsMixin
from doxabase.core.query_evidence import QueryEvidenceMixin
from doxabase.core.query_repair import QueryRepairMixin
from doxabase.core.query_plans import QueryPlansMixin
from doxabase.core.revision_snapshots import RevisionSnapshotsMixin
from doxabase.core.lineage import LineageMixin
from doxabase.core.query_planning import QueryPlanningMixin
from doxabase.core.revisions import RevisionsMixin
from doxabase.core.staging import StagingMixin
from doxabase.core.staging_describe import StagingDescribeMixin
from doxabase.core.staging_apply import StagingApplyMixin
from doxabase.core.staging_review import StagingReviewMixin
from doxabase.core.restage import RestageMixin
from doxabase.core.recovery import RecoveryMixin
from doxabase.core.systematisation import SystematisationMixin
from doxabase.core.exports import ExportsMixin
from doxabase.core.privacy import PrivacyMixin
from doxabase.core.validation import ValidationMixin


class DoxaBase(
    StorageMixin,
    SearchMixin,
    EntitiesMixin,
    DatasetsMixin,
    SlicesMixin,
    BriefMixin,
    ObservationsMixin,
    MapAuthoringMixin,
    ProfilesMixin,
    ProfileRecordsMixin,
    ProfileReviewMixin,
    ProfilePromotionMixin,
    ProfileAdvisoriesMixin,
    MapStagingMixin,
    AnalysisViewsMixin,
    QueryEvidenceMixin,
    QueryRepairMixin,
    QueryPlansMixin,
    RevisionSnapshotsMixin,
    LineageMixin,
    QueryPlanningMixin,
    RevisionsMixin,
    StagingMixin,
    StagingDescribeMixin,
    StagingApplyMixin,
    StagingReviewMixin,
    RestageMixin,
    RecoveryMixin,
    SystematisationMixin,
    ExportsMixin,
    PrivacyMixin,
    ValidationMixin,
):
    """A small SQLite-backed RDF memory capsule.

V1 stores RDF terms as strings in a simple quad table. RDFLib handles
parsing/serialization and pySHACL handles explicit validation.
    """


# Some methods reference `DoxaBase` at runtime (staticmethod cross-calls,
# `object.__new__(DoxaBase)` in the preflight clone). The mixin modules cannot
# import the composed class without a cycle, so bind it into each mixin
# module's globals after composition. Transitional: Phase 3/4 waves should
# rewrite those call sites (`type(self)` / `cls`) and delete this loop.
import sys as _sys  # noqa: E402

for _mixin_module in (
    "storage", "search", "entities", "datasets", "slices", "brief",
    "observations", "map_authoring", "profiles", "profile_records",
    "profile_review", "profile_promotion", "profile_advisories",
    "map_staging", "analysis_views", "query_evidence", "query_repair",
    "query_plans", "revision_snapshots", "lineage", "query_planning",
    "revisions", "staging", "staging_describe", "staging_apply",
    "staging_review", "restage", "recovery", "systematisation", "exports",
    "privacy", "validation",
):
    _sys.modules[f"doxabase.core.{_mixin_module}"].DoxaBase = DoxaBase  # type: ignore[attr-defined]
del _sys, _mixin_module
