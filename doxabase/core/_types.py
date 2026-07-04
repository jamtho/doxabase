"""Response and record types for doxabase.core (mechanical split).

Order preserved from the original module; classes may depend on earlier
ones (inheritance) and on _shared constants.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403

class DoxaBaseError(Exception):
    """Base exception for DoxaBase runtime errors."""


class ImmutableGraphError(DoxaBaseError):
    """Raised when a caller tries to mutate an immutable graph."""


@dataclass(frozen=True)
class NamedGraphInfo:
    name: str
    description: str | None
    mutable: bool
    system_seed: bool
    source_path: str | None
    triple_count: int


@dataclass(frozen=True)
class GraphOverview:
    named_graphs: list[NamedGraphInfo]
    class_counts: list[tuple[str, int]]
    predicate_counts: list[tuple[str, int]]
    key_counts: dict[str, int]
    namespaces: dict[str, str]


@dataclass(frozen=True)
class ProjectBriefDatasetQuerySummary:
    readiness: str
    readiness_note: str
    issue_codes: list[str]
    repair_action_group_count: int
    candidate_count: int
    ready_candidate_indexes: list[int]
    direct_clean_candidate_indexes: list[int]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ProjectBriefProfileDraftSummary:
    evidence_iri: str
    status: str
    requires_review: bool
    profile_observation_count: int
    recommendation_count: int
    scalar_conflict_group_count: int
    metric_advisory_count: int
    metric_advisory_status_counts: dict[str, int]
    type_advisory_count: int
    type_advisory_status_counts: dict[str, int]
    action_group_names: list[str]
    pending_staged_profile_advisory_iris: list[str]
    pending_staged_profile_advisory_count: int
    pending_staged_profile_advisory_actions: list[SuggestedNextAction]
    pending_staged_profile_advisory_calls: list[str]
    task_advisories: list[dict[str, Any]]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ProjectBriefDatasetProfileSummary:
    total_profile_count: int
    returned_profile_count: int
    omitted_profile_count: int
    profile_evidence_count: int
    profile_evidence_iris: list[str]
    profile_run_candidate_count: int
    profile_run_evidence_iris: list[str]
    draft_candidate_count: int
    profile_candidate_omitted_count: int
    omitted_draft_evidence_iris: list[str]
    draft_count: int
    review_draft_count: int
    completed_draft_count: int
    draft_status_counts: dict[str, int]
    draft_evidence_iris: list[str]
    drafts: list[ProjectBriefProfileDraftSummary]


@dataclass(frozen=True)
class ProjectBriefDatasetSummary:
    dataset: ResourceSummary
    is_table: bool
    query: ProjectBriefDatasetQuerySummary
    profile: ProjectBriefDatasetProfileSummary


@dataclass(frozen=True)
class ProjectBriefStagedReviewItem:
    revision_iri: str
    summary: str | None
    record_kind: str
    application_status: str | None
    queue: str | None
    resolved_target_iri: str | None
    revision_anchor_iris: list[str]
    evidence_iris: list[str]
    suggested_next_action: SuggestedNextAction | None


@dataclass(frozen=True)
class ProjectBriefStagedReviewSummary:
    count: int
    returned_count: int
    omitted_count: int
    application_status_counts: dict[str, int]
    next_action_queue_item_counts: dict[str, int]
    items: list[ProjectBriefStagedReviewItem]


@dataclass(frozen=True)
class ProjectBriefRecommendedTask:
    priority: int
    task_type: str
    source: str
    resource: ResourceSummary | None
    reason: str
    suggested_next_action: SuggestedNextAction | None
    suggested_next_call: str | None
    inspection_next_action: SuggestedNextAction | None = None
    inspection_next_call: str | None = None
    profile_evidence_iri: str | None = None
    pending_staged_repair_iris: list[str] = field(default_factory=list)
    pending_staged_profile_update_iris: list[str] = field(default_factory=list)
    query_plan_handoff_summary: DraftQueryPlanHandoffSummary | None = None
    task_advisories: list[dict[str, Any]] = field(default_factory=list)
    task_group: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProjectBriefHealthTask:
    priority: int
    task_type: str
    source: str
    reason: str
    suggested_next_action: SuggestedNextAction | None
    suggested_next_call: str | None
    queue_types: list[str] = field(default_factory=list)
    omitted_queue_counts: dict[str, int] = field(default_factory=dict)
    suggested_limit: int | None = None
    exhaustive_suggested_limit: int | None = None
    suggested_profile_candidate_limit: int | None = None
    profile_candidate_omitted_count: int | None = None
    sensitive_literal_count: int | None = None
    would_block_invalid_export: bool | None = None
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int | None = None
    missing_seed_terms: list[str] = field(default_factory=list)
    current_staged_revision_count: int | None = None
    fixture_names: list[str] = field(default_factory=list)
    known_fixture_table_iris: list[str] = field(default_factory=list)
    storage_access_count: int | None = None


@dataclass(frozen=True)
class ProjectBriefFrontierStatus:
    is_complete: bool
    hidden_task_count: int
    hidden_profile_candidate_count: int
    hidden_queue_types: list[str]
    active_queue_types: list[str]
    returned_queue_types: list[str]
    must_rerun_call: str | None
    safety_first_call: str | None
    frontier_first_call: str | None
    first_unattended_call: str | None
    first_unattended_source: str | None
    mutation_allowed_after: str
    note: str


@dataclass(frozen=True)
class ProjectBrief:
    key_counts: dict[str, int]
    dataset_count: int
    returned_dataset_count: int
    dataset_query_readiness_counts: dict[str, int]
    returned_dataset_query_readiness_counts: dict[str, int]
    profile_queue_counts: dict[str, int]
    queue_counts: dict[str, int]
    returned_queue_counts: dict[str, int]
    omitted_queue_counts: dict[str, int]
    active_queue_type_count: int
    returned_queue_type_count: int
    limit_crowded_queue_types: list[str]
    health_tasks: list[ProjectBriefHealthTask]
    next_best_expansion: ProjectBriefHealthTask | None
    full_frontier_expansion: ProjectBriefHealthTask | None
    safety_first_action: SuggestedNextAction | None
    safety_first_call: str | None
    safety_first_source: str | None
    frontier_first_action: SuggestedNextAction | None
    frontier_first_call: str | None
    frontier_first_source: str | None
    first_unattended_action: SuggestedNextAction | None
    first_unattended_call: str | None
    first_unattended_source: str | None
    frontier_status: ProjectBriefFrontierStatus
    datasets: list[ProjectBriefDatasetSummary]
    staged_review: ProjectBriefStagedReviewSummary
    recommended_next_tasks: list[ProjectBriefRecommendedTask]
    limit: int
    profile_candidate_limit: int


@dataclass(frozen=True)
class SensitiveLiteralMatch:
    graph: str
    subject: str
    predicate: str
    object_kind: str
    term_position: str
    term_kind: str
    match_kind: str
    redacted_snippet: str


@dataclass(frozen=True)
class SensitiveLiteralScan:
    graphs: list[str]
    match_count: int
    sensitive_literal_count: int
    returned_match_count: int
    omitted_match_count: int
    limit: int
    matches: list[SensitiveLiteralMatch]
    warnings: list[str]


@dataclass(frozen=True)
class ExportPreflightMatch:
    export_part: str
    match_id: str
    graph: str
    subject: str
    predicate: str
    object_kind: str
    term_position: str
    term_kind: str
    match_kind: str
    redacted_snippet: str
    revision_iri: str | None = None


@dataclass(frozen=True)
class ShareabilityHintMatch:
    export_part: str
    match_id: str
    hint_code: str
    graph: str | None = None
    subject: str | None = None
    predicate: str | None = None
    object_kind: str | None = None
    term_position: str | None = None
    term_kind: str | None = None
    revision_iri: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class ExportPreflightRecord:
    export_kind: str
    decision: str
    scanner_clean: bool
    shareability_review_required: bool
    shareability_review_status: str
    would_block_sensitive_export: bool
    graphs: list[str]
    graph_counts: dict[str, int]
    revision_iris: list[str]
    snapshot_graph_roles: list[str]
    snapshot_count: int
    snapshot_quad_count: int
    sensitive_literal_count: int
    graph_sensitive_literal_count: int
    snapshot_sensitive_literal_count: int
    returned_match_count: int
    omitted_match_count: int
    limit: int
    matches: list[ExportPreflightMatch]
    privacy_warnings: list[str]
    warnings: list[str]
    scanner_note: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int = 0
    validation_results: list[ValidationDiagnostic] = field(default_factory=list)
    would_block_invalid_export: bool = False
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class GraphExportRecord:
    path: str
    format: str
    graphs: list[str]
    graph_counts: dict[str, int]
    triples: int
    bytes_written: int
    sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int = 0
    validation_results: list[ValidationDiagnostic] = field(default_factory=list)
    would_block_invalid_export: bool = False
    artifact_kind: str = "graph_rdf_export"
    importable: bool = True
    recommended_import_tool: str | None = "DoxaBase.import_turtle"
    recovery_complete: bool = False
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class ContextSliceExportRecord:
    path: str | None
    format: str
    decision: str
    scanner_clean: bool
    shareability_review_required: bool
    shareability_review_status: str
    would_block_sensitive_export: bool
    handoff_fit: str
    profile: str
    seeds: list[ResourceSummary]
    graphs: list[str]
    graph_counts: dict[str, int]
    triples: int
    candidate_triple_count: int
    omitted_triple_count: int
    max_triples: int
    truncated: bool
    include_seed_graphs: bool
    bytes_written: int
    sensitive_literal_count: int
    returned_match_count: int
    omitted_match_count: int
    limit: int
    matches: list[SensitiveLiteralMatch]
    privacy_warnings: list[str]
    warnings: list[str]
    scanner_note: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int = 0
    validation_results: list[ValidationDiagnostic] = field(default_factory=list)
    would_block_invalid_export: bool = False
    artifact_kind: str = "context_slice_trig"
    importable: bool = True
    recommended_import_tool: str | None = "doxabase.import_trig"
    recovery_complete: bool = False
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class GraphTripleReplacementRecord:
    graph: str
    format: str
    before_count: int
    after_count: int
    count_delta: int
    before_digest: str
    after_digest: str
    digest_changed: bool
    removal_triples: int
    addition_triples: int
    triples_removed: int
    triples_added: int
    same_count: bool
    expected_count: int | None
    allow_count_change: bool


@dataclass(frozen=True)
class GraphRevisionRecord:
    revision_iri: str
    revision_type: str
    graph: str
    triples: int


@dataclass(frozen=True)
class StagedRevisionReviewResolutionSummary:
    resolution_revision_iri: str
    decision: str
    decision_iri: str | None
    decision_label: str | None
    summary: str | None
    rationale: str | None
    created_at: str | None
    created_by: str | None


@dataclass(frozen=True)
class StagedRevisionReviewDecisionRecord:
    resolution_revision_iri: str
    staged_revision_iri: str
    decision: str
    decision_iri: str
    graph: str
    triples: int
    current_application_status: str | None
    current_stale_resolution_state: str | None
    current_next_action: RevisionNextAction | None
    closes_current_staged_work: bool
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class RevisionSnapshotBundleExportRecord:
    path: str
    format: str
    revision_iris: list[str]
    graph_roles: list[str]
    snapshot_count: int
    quad_count: int
    bytes_written: int
    sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    artifact_kind: str = "revision_snapshot_bundle"
    importable: bool = True
    recommended_import_tool: str | None = "doxabase.import_revision_snapshots"
    recovery_complete: bool = False
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class HandoffBundleExportRecord:
    trig: GraphExportRecord
    revision_snapshots: RevisionSnapshotBundleExportRecord
    paths: dict[str, str]
    manifest: dict[str, Any]
    graph_roles: list[str]
    snapshot_graph_roles: list[str]
    revision_iris: list[str]
    manifest_path: str | None = None
    manifest_bytes_written: int | None = None
    decision: str = "clean_by_scanner_only"
    scanner_clean: bool = True
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    would_block_sensitive_export: bool = False
    sensitive_literal_count: int = 0
    graph_sensitive_literal_count: int = 0
    snapshot_sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int = 0
    validation_results: list[ValidationDiagnostic] = field(default_factory=list)
    would_block_invalid_export: bool = False
    scanner_note: str = (
        "Scanner-clean means no selected export content matched DoxaBase's "
        "credential-like graph-term patterns; it is not proof that an artifact "
        "is shareable or free of user-specific paths, endpoint details, or "
        "confidential project facts."
    )
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False
    artifact_kind: str = "handoff_bundle"
    importable: bool = True
    recommended_import_tool: str | None = (
        "doxabase.import_trig then doxabase.import_revision_snapshots"
    )
    recovery_complete: bool = True


@dataclass(frozen=True)
class RevisionSnapshotBundleImportRecord:
    path: str
    format: str
    replace: bool
    revision_iris: list[str]
    graph_roles: list[str]
    snapshot_count: int
    imported_snapshot_count: int
    skipped_snapshot_count: int
    quad_count: int
    imported_quad_count: int
    post_import_snapshot_evidence: list[RevisionSnapshotEvidenceStatus]


@dataclass(frozen=True)
class HandoffBundleRecoverySummary:
    result_kind: str
    dry_run: bool
    revision_count: int
    snapshot_evidence_complete: bool
    snapshot_evidence_status_counts: dict[str, int]
    incomplete_snapshot_revision_iris: list[str]
    trig_total_imported: int
    imported_snapshot_count: int
    skipped_snapshot_count: int
    imported_recovery_session_count: int
    imported_recovery_session_iris: list[str]
    matching_recovery_session_count: int
    matching_recovery_session_iris: list[str]
    resume_recovery_session_iri: str | None
    resume_recovery_session_call: str | None
    recovery_plan_available: bool
    recovery_lane_counts: dict[str, int]
    recovery_next_action_queue_item_counts: dict[str, int]
    mutation_frontier_iris: list[str]
    mutation_frontier_count: int
    first_mutation_frontier_item: StagedRevisionMutationFrontierItem | None
    first_mutation_action: SuggestedNextAction | RevisionNextAction | None
    first_safe_review_or_mutation_action: (
        SuggestedNextAction | RevisionNextAction | None
    )
    first_safe_review_or_mutation_call: str | None
    first_safe_review_or_mutation_source: str | None
    profile_route_revision_count: int
    profile_route_group_count: int
    profile_route_keys: list[str]
    first_suggested_next_action: SuggestedNextAction | None
    recommended_next_step: str
    note: str


@dataclass(frozen=True)
class HandoffBundleImportRecord:
    path: str
    format: str
    dry_run: bool
    replace: bool
    manifest: dict[str, Any]
    paths: dict[str, str]
    graph_roles: list[str]
    snapshot_graph_roles: list[str]
    revision_iris: list[str]
    pre_import_snapshot_evidence: list[RevisionSnapshotEvidenceStatus]
    trig_imported: dict[str, int]
    trig_total_imported: int
    post_trig_snapshot_evidence: list[RevisionSnapshotEvidenceStatus]
    revision_snapshots: RevisionSnapshotBundleImportRecord | None
    post_import_snapshot_evidence: list[RevisionSnapshotEvidenceStatus]
    recovery_plan: StagedRevisionRecoveryPlan | None
    imported_recovery_session_iris: list[str]
    matching_recovery_session_iris: list[str]
    recovery_summary: HandoffBundleRecoverySummary
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    warnings: list[str]
    artifact_kind: str = "handoff_bundle_import"
    recovery_complete: bool = True


@dataclass(frozen=True)
class StagedGraphPatchRecord:
    patch_iri: str
    operation: str
    target_graph: str
    count_basis: str
    format: str
    patch_role: str
    sequence_index: int
    triple_count: int
    before_triple_count: int
    after_triple_count: int


@dataclass(frozen=True)
class ValidationDiagnostic:
    iri: str | None
    focus_node: str | None
    focus_node_label: str | None
    result_path: str | None
    result_path_label: str | None
    value: str | None
    source_shape: str | None
    source_constraint_component: str | None
    source_constraint_component_label: str | None
    severity: str | None
    severity_label: str | None
    messages: list[str]
    hint: str | None = None


@dataclass(frozen=True)
class StagedGraphRevisionRecord:
    revision_iri: str
    revision_type: str
    revision_stance: str
    summary: str
    rationale: str
    review_note: str | None
    review_recommendation: str | None
    graph: str
    triples: int
    changed_graphs: list[str]
    patches: list[StagedGraphPatchRecord]
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]
    alternative_to: str | None = None
    restaged_from: str | None = None
    restage_reason: str | None = None
    current_restaged_by: str | None = None
    framing_index: int | None = None
    framing_label: str | None = None


@dataclass(frozen=True)
class RestagedGraphRevisionRecord(StagedGraphRevisionRecord):
    status_after: str | None = None
    decision_after: str | None = None
    routing_decision_after: str | None = None
    stale_resolution_state_after: str | None = None
    blocking_reasons_after: list[str] = field(default_factory=list)
    current_staged_validation_status: str | None = None
    next_action_after: RevisionNextAction | None = None
    next_action_queue_item_after: RevisionNextActionQueueItem | None = None
    suggested_next_actions_after: list[SuggestedNextAction] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class StagedPatchApplyCheck:
    patch_iri: str
    target_graph: str | None
    count_basis: str | None
    operation: str | None
    operation_label: str | None
    patch_role: str | None
    patch_role_label: str | None
    triple_count: int | None
    before_triple_count: int | None
    current_triple_count: int | None
    after_triple_count: int | None
    preview_triple_count: int | None
    effective_triples_to_add: int | None
    effective_triples_to_remove: int | None
    already_present_triples: int | None
    already_absent_triples: int | None
    can_apply: bool
    conflict: str | None


@dataclass(frozen=True)
class StagedPatchRepairPlan:
    patch_iri: str
    patch_sequence_index: int | None
    target_graph: str | None
    operation: str | None
    operation_label: str | None
    patch_role: str | None
    patch_role_label: str | None
    triple_count: int | None
    patch_triple_status: str | None
    effect_class: str
    recommended_action_kind: str
    action: SuggestedNextAction | None
    current_same_subject_predicate_triples: list[ResourceTriple]
    proposed_triples: list[GraphTripleDescription]
    note: str


@dataclass(frozen=True)
class StagedRevisionEffectiveDeltaSummary:
    replayable_triples_to_add: int
    replayable_triples_to_remove: int
    blocked_patch_triples_to_add: int
    blocked_patch_triples_to_remove: int
    total_effective_triples_to_add: int
    total_effective_triples_to_remove: int
    already_effective: bool
    has_conflicted_patches: bool
    patch_triple_status_counts: dict[str, int]
    basis: str
    note: str


@dataclass(frozen=True)
class StagedRevisionAlternativeGate:
    status: str
    alternative_to: str | None
    current_alternative_to: str | None
    applied_source_iri: str | None
    applied_revision_iri: str | None
    semantic_review_required: bool
    note: str


@dataclass(frozen=True)
class StagedGraphCountDrift:
    patch_iri: str
    patch_sequence_index: int | None
    target_graph: str
    count_basis: str
    expected_before_triple_count: int
    expected_before_basis: str
    current_triple_count: int
    delta: int
    exact_changed_triples_available: bool
    patch_operation: str | None
    patch_operation_label: str | None
    patch_triples_checked: int | None
    patch_triples_currently_present: int | None
    patch_triples_currently_absent: int | None
    patch_triple_status: str | None
    note: str


@dataclass(frozen=True)
class GraphTripleDescription:
    subject: str
    subject_kind: str
    subject_curie: str | None
    subject_display: str
    predicate: str
    predicate_curie: str | None
    predicate_display: str
    object: str
    object_kind: str
    object_curie: str | None
    object_display: str
    datatype: str | None
    lang: str | None


@dataclass(frozen=True)
class ChangedGraphResourceSummary:
    resource: ResourceSummary
    changed_triple_count: int
    added_triple_count: int
    removed_triple_count: int
    matched_by: list[str]
    predicate_iris: list[str]
    predicate_displays: list[str]


@dataclass(frozen=True)
class StagedGraphSnapshotDrift:
    graph_role: str
    snapshot_triple_count: int
    current_triple_count: int
    snapshot_content_digest: str
    current_content_digest: str
    exact_changed_triples_available: bool
    exact_changed_triples_included: bool
    triples_added_since_snapshot_count: int | None
    triples_removed_since_snapshot_count: int | None
    drift_relevance: str
    patch_overlap_subjects: list[str]
    patch_overlap_predicates: list[str]
    patch_overlap_objects: list[str]
    revision_anchor_overlap: list[str]
    changed_resource_count: int | None
    changed_resources_returned_count: int
    changed_resources_omitted_count: int | None
    changed_resources: list[ChangedGraphResourceSummary]
    changed_resource_suggested_next_actions: list[SuggestedNextAction]
    triples_added_since_snapshot: list[GraphTripleDescription]
    triples_removed_since_snapshot: list[GraphTripleDescription]
    note: str


@dataclass(frozen=True)
class StagedRevisionExactDriftSummary:
    graph_role: str
    blocking_reasons: list[str]
    has_count_drift: bool
    has_snapshot_digest_drift: bool
    count_drift_count: int
    count_drift_deltas: list[int]
    patch_triple_status_counts: dict[str, int]
    snapshot_triple_count: int | None
    current_triple_count: int | None
    triples_added_since_snapshot_count: int | None
    triples_removed_since_snapshot_count: int | None
    exact_changed_triples_available: bool
    exact_changed_triples_included: bool
    drift_relevance: str | None
    changed_resource_count: int | None
    changed_resources_returned_count: int
    changed_resources_omitted_count: int | None
    changed_resources: list[ChangedGraphResourceSummary]
    changed_resource_suggested_next_actions: list[SuggestedNextAction]
    note: str


@dataclass(frozen=True)
class AppliedRevisionGraphSnapshotDiff:
    graph_role: str
    count_basis: str
    before_revision_iri: str
    after_revision_iri: str
    before_triple_count: int | None
    after_triple_count: int | None
    before_content_digest: str | None
    after_content_digest: str | None
    exact_changed_triples_available: bool
    exact_changed_triples_included: bool
    triples_added_count: int | None
    triples_removed_count: int | None
    triples_added_truncated: bool
    triples_removed_truncated: bool
    max_triples: int
    triples_added: list[GraphTripleDescription]
    triples_removed: list[GraphTripleDescription]
    note: str


@dataclass(frozen=True)
class AppliedRevisionDiffDescription:
    applied_revision_iri: str
    staged_revision_iri: str
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    source_snapshot_evidence: RevisionSnapshotEvidenceStatus
    changed_graphs: list[str]
    include_triples: bool
    max_triples: int
    graph_diffs: list[AppliedRevisionGraphSnapshotDiff]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class StagedRevisionApplyCheck:
    staged_revision_iri: str
    revision_iri: str
    can_apply: bool
    status: str
    decision: str
    routing_decision: str
    summary: str
    review_recommended: bool
    semantic_risk_level: str
    semantic_risk_reasons: list[str]
    blocking_reasons: list[str]
    recommended_resolution: str | None
    already_applied_by: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    stale_resolution_state: str | None
    alternative_gate: StagedRevisionAlternativeGate
    changed_graphs: list[str]
    patch_checks: list[StagedPatchApplyCheck]
    patch_repair_plan: list[StagedPatchRepairPlan]
    count_drifts: list[StagedGraphCountDrift]
    snapshot_drifts: list[StagedGraphSnapshotDrift]
    conflicts: list[str]
    validation_scope: str
    validation_conforms: bool | None
    validation_skipped_reason: str | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    patches_checked: int
    triples_to_add: int
    triples_to_remove: int
    effective_delta_summary: StagedRevisionEffectiveDeltaSummary
    next_action: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    snapshot_evidence: RevisionSnapshotEvidenceStatus | None = None
    snapshot_evidence_completeness: str = "unknown"
    blocking_preflight_actions: list[SuggestedNextAction] = field(
        default_factory=list
    )
    blocking_preflight_calls: list[str] = field(default_factory=list)
    mutation_allowed_after: str = "direct_check_no_preflight"
    first_safe_next_action: RevisionNextAction | None = None
    first_safe_next_call: str | None = None


@dataclass(frozen=True)
class StagedRevisionApplySummary:
    staged_revision_iri: str
    status: str
    decision: str | None
    routing_decision: str | None
    can_apply: bool | None
    summary: str | None
    review_recommended: bool | None
    semantic_risk_level: str | None
    semantic_risk_reasons: list[str]
    blocking_reasons: list[str]
    recommended_resolution: str | None
    already_applied_by: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    stale_resolution_state: str | None
    alternative_gate: StagedRevisionAlternativeGate
    changed_graphs: list[str]
    validation_scope: str | None
    validation_conforms: bool | None
    validation_skipped_reason: str | None
    validation_result_count: int | None
    patches_checked: int | None
    triples_to_add: int | None
    triples_to_remove: int | None
    effective_delta_summary: StagedRevisionEffectiveDeltaSummary | None
    count_drifts: list[StagedGraphCountDrift]
    snapshot_drifts: list[StagedGraphSnapshotDrift]
    next_action: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    error: str | None


@dataclass(frozen=True)
class StagedRevisionRebaseLineageContext:
    selected_revision_iri: str
    current_staged_revision_iri: str | None
    current_revision_iri: str | None
    latest_revision_iri: str | None
    latest_role: str | None
    restage_chain_iris: list[str]
    alternative_revision_iris: list[str]
    related_revision_iris: list[str]
    alternative_to: str | None
    current_alternative_to: str | None
    alternative_gate_status: str
    alternative_semantic_review_required: bool
    alternative_applied_source_iri: str | None
    alternative_applied_revision_iri: str | None


@dataclass(frozen=True)
class StagedRevisionRebaseCandidate:
    candidate_kind: str
    candidate_status: str
    graph: str
    subject: str
    predicate: str
    object: str | None
    object_kind: str
    object_datatype: str | None
    object_lang: str | None
    current_same_subject_predicate_triples: list[ResourceTriple]
    proposed_triples: list[GraphTripleDescription]
    validation_results: list[ValidationDiagnostic]
    action: SuggestedNextAction
    note: str


@dataclass(frozen=True)
class StagedRevisionRebaseDraft:
    result_kind: str
    helper: str
    mode: str
    source_revision_iri: str
    current_revision_iri: str
    draft_status: str
    draft_kind: str
    reason_codes: list[str]
    source_staged_validation_status: str
    apply_check: StagedRevisionApplyCheck
    lineage: StagedRevisionRebaseLineageContext
    validation_results: list[ValidationDiagnostic]
    repair_candidates: list[StagedRevisionRebaseCandidate]
    repair_actions: list[SuggestedNextAction]
    preferred_action: SuggestedNextAction | None
    next_action: RevisionNextAction | None
    next_action_queue_item: RevisionNextActionQueueItem | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    note: str


@dataclass(frozen=True)
class SystematisationFramingRecord:
    label: str
    rationale: str | None
    review_note: str | None
    review_recommendation: str | None
    target_graphs: list[str]
    stance: str
    revision_iri: str
    patch_count: int
    triple_count: int
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class SystematisationSharedPatchSummary:
    target_graph: str
    operation: str
    operation_label: str | None
    patch_role: str
    patch_role_label: str | None
    sequence_index: int
    triple_count: int
    count_basis: str
    format: str


@dataclass(frozen=True)
class SystematisationWarningRecord:
    warning_code: str
    message: str
    affected_revision_iris: list[str]
    suggested_action: str
    suggested_rerun_arguments: dict[str, Any]
    shared_patch_summaries: list[SystematisationSharedPatchSummary] = field(
        default_factory=list
    )
    fallback_revision_iris_with_shared_semantic_context: list[str] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class SharedSemanticContextBundleWarning:
    warning_code: str
    message: str
    affected_revision_iris: list[str]
    shared_context_graphs: list[str]
    shared_context_patch_summaries: list[SystematisationSharedPatchSummary]
    fallback_revision_iris_with_shared_semantic_context: list[str]
    suggested_action: str


@dataclass(frozen=True)
class SystematisationDraftRecord:
    result_kind: str
    summary: str
    intent: str
    anchors: list[str]
    profile_route_source_count: int
    warnings: list[str]
    structured_warnings: list[SystematisationWarningRecord]
    framings: list[SystematisationFramingRecord]
    staged_revisions: list[StagedGraphRevisionRecord]
    next_action_queue: dict[str, list[str]]
    next_action_queue_items: list[RevisionNextActionQueueItem]
    next_action_queue_item_counts: dict[str, int]
    choose_one_groups: list["StagedGraphRevisionChooseOneGroup"]
    choose_one_group_count: int
    semantic_review_required_queue_counts: dict[str, int]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class SystematisationSharedContextRerunFraming:
    source_revision_iri: str
    label: str
    receives_shared_context: bool
    moved_shared_patch_count: int
    framing_patch_count: int
    target_graphs: list[str]
    validation_scope: str | None


@dataclass(frozen=True)
class SystematisationSharedContextRerunDraft:
    result_kind: str
    helper: str
    mode: str
    source_revision_iris: list[str]
    shared_context_target_revision_iris: list[str]
    shared_context_graphs: list[str]
    shared_context_patch_summaries: list[SystematisationSharedPatchSummary]
    framings: list[SystematisationSharedContextRerunFraming]
    stage_systematisation_arguments: dict[str, Any]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    warnings: list[str]
    note: str


@dataclass(frozen=True)
class PostApplyRecheckRevision:
    iri: str
    changed_graphs: list[str]
    shared_changed_graphs: list[str]
    recheck_reasons: list[str]
    application_status: str
    decision: str
    routing_decision: str
    blocking_reasons: list[str]
    next_action: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class AppliedStagedRevisionRecord:
    applied_revision_iri: str
    staged_revision_iri: str
    graph: str
    triples: int
    changed_graphs: list[str]
    post_apply_recheck_revisions: list[PostApplyRecheckRevision]
    post_apply_recheck_revision_iris: list[str]
    post_apply_recheck_is_partial_queue: bool
    warnings: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    patches_applied: int
    triples_added: int
    triples_removed: int
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class StagedGraphRevisionExportRecord:
    path: str
    format: str
    revision_iri: str
    bytes_written: int
    sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    decision: str = "clean_by_scanner_only"
    scanner_clean: bool = True
    would_block_sensitive_export: bool = False
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False
    artifact_kind: str = "staged_revision_review_markdown"
    importable: bool = False
    recommended_import_tool: str | None = None
    recovery_complete: bool = False


@dataclass(frozen=True)
class StagedGraphRevisionExportSummary:
    revision_iri: str
    summary: str | None
    revision_stance: str | None
    revision_stance_label: str | None
    alternative_to: str | None
    current_alternative_to: str | None
    alternative_gate: StagedRevisionAlternativeGate
    changed_graphs: list[str]
    apply_status: str | None
    apply_decision: str | None
    apply_can_apply: bool | None
    apply_summary: str | None
    apply_recommended_resolution: str | None
    apply_recommendation_scope: str | None
    apply_blocking_reasons: list[str]
    apply_validation_conforms: bool | None
    apply_validation_skipped_reason: str | None
    apply_validation_result_count: int | None
    apply_check_error: str | None
    semantic_risk_level: str | None
    semantic_risk_reasons: list[str]
    current_validation: str
    staged_validation: str
    staged_validation_conforms: bool | None
    staged_validation_result_count: int | None
    validation_diagnostic_headline: str
    review_recommendation: str | None
    summary_recommendation: str
    summary_recommendation_source: str
    active_recommendation_field: str
    restaged_from: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    stale_resolution_state: str | None
    shared_context_patch_count: int
    shared_context_graphs: list[str]
    profile_route_keys: list[str]
    profile_route_groups: list[dict[str, Any]]
    next_action: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class StagedGraphRevisionSnapshotEvidenceRow:
    row_index: int
    revision_iri: str
    summary: str | None
    status: str
    completeness: str
    rdf_snapshot_graph_roles: list[str]
    stored_snapshot_graph_roles: list[str]
    exact_snapshot_graph_roles: list[str]
    missing_snapshot_row_graph_roles: list[str]
    orphan_snapshot_row_graph_roles: list[str]
    note: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class StagedGraphRevisionSnapshotEvidenceSummary:
    complete: bool
    total_revision_count: int
    incomplete_revision_iris: list[str]
    status_counts: dict[str, int]
    rows: list[StagedGraphRevisionSnapshotEvidenceRow]


@dataclass(frozen=True)
class StagedGraphRevisionReviewSequenceItem:
    phase: str
    phase_label: str
    row_index: int
    row_iri: str
    summary: str | None
    queue: str
    resolved_target_iri: str | None
    resolved_target_record_kind: str | None
    tool_name: str | None
    mcp_tool_name: str | None
    action_label: str
    reason: str


@dataclass(frozen=True)
class StagedGraphRevisionChooseOneGroup:
    group_index: int
    row_indexes: list[int]
    revision_iris: list[str]
    summaries: list[str | None]
    alternative_set_source_iri: str | None
    source_row_index: int | None
    source_summary: str | None
    alternative_set_roles: list[str | None]


@dataclass(frozen=True)
class StagedGraphRevisionModellingChoiceRow:
    row_index: int
    revision_iri: str
    summary: str | None
    modelling_role: str
    role_source: str
    role_reason: str
    queue: str | None
    apply_status: str | None
    apply_decision: str | None
    current_validation: str
    staged_validation: str
    changed_graphs: list[str]
    alternative_set_role: str | None
    shared_context_applies: bool
    shared_context_graphs: list[str]
    support_counts: dict[str, int]
    support_note: str
    recommended_human_action: str


@dataclass(frozen=True)
class StagedGraphRevisionBundleSummary:
    total_revisions: int
    decision_headline: str
    apply_status_counts: dict[str, int]
    stale_resolution_state_counts: dict[str, int]
    changed_graph_counts: dict[str, int]
    choose_one_groups: list[StagedGraphRevisionChooseOneGroup]
    modelling_choice_summary: str | None
    modelling_choice_rows: list[StagedGraphRevisionModellingChoiceRow]
    unresolved_stale_revision_iris: list[str]
    stale_handled_by_restage_revision_iris: list[str]
    ready_restage_successor_revision_iris: list[str]
    ready_restage_successor_alternative_to_applied_source_iris: list[str]
    post_apply_recheck_revision_iris: list[str]
    sequential_apply_recheck_candidate_iris: list[str]
    warnings: list[str]
    validation_failed_revision_iris: list[str]
    staged_validation_failed_revision_iris: list[str]
    recommended_review_iris: list[str]
    external_recommended_review_iris: list[str]
    recommended_mutation_review_iris: list[str]
    recommended_apply_or_restage_review_iris: list[str]
    recommended_repair_review_iris: list[str]
    recommended_applied_inspection_iris: list[str]
    review_sequence: list[StagedGraphRevisionReviewSequenceItem]
    next_action_queue: dict[str, list[str]]
    next_action_queue_items: list[RevisionNextActionQueueItem]
    next_action_queue_item_counts: dict[str, int]
    snapshot_evidence: StagedGraphRevisionSnapshotEvidenceSummary
    mutation_frontier_iris: list[str]
    requires_recheck_after_each_apply: bool
    semantic_risk_queue_counts: dict[str, int]
    semantic_review_required_queue_counts: dict[str, int]
    shared_context_graphs: list[str]
    shared_context_patch_summaries: list[SystematisationSharedPatchSummary]
    fallback_revision_iris_with_shared_semantic_context: list[str]
    shared_semantic_context_warnings: list[SharedSemanticContextBundleWarning]


@dataclass(frozen=True)
class StagedGraphRevisionsExportRecord:
    path: str
    format: str
    revision_iris: list[str]
    revision_count: int
    bytes_written: int
    revision_summaries: list[StagedGraphRevisionExportSummary]
    bundle_summary: StagedGraphRevisionBundleSummary
    sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    decision: str = "clean_by_scanner_only"
    scanner_clean: bool = True
    would_block_sensitive_export: bool = False
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False
    artifact_kind: str = "staged_revisions_review_markdown"
    importable: bool = False
    recommended_import_tool: str | None = None
    recovery_complete: bool = False


@dataclass(frozen=True)
class ProfileInsightReviewCandidate:
    revision_iri: str
    summary: str | None
    changed_graphs: list[str]
    relation_reasons: list[str]
    profile_route_keys: list[str]
    profile_route_groups: list[dict[str, Any]]
    matched_evidence_iris: list[str]
    matched_profile_observation_iris: list[str]
    matched_supporting_pattern_iris: list[str]
    matched_revision_anchor_iris: list[str]
    explicit: bool
    semantic_apply_role: str = "supporting_context"
    semantic_choice_group_key: str | None = None
    apply_cardinality: str = "inspect_only"
    bulk_apply_allowed: bool = False
    safe_single_apply_candidate: bool = False
    profile_quality_summary: dict[str, Any] = field(default_factory=dict)
    sampled_evidence_caution: str | None = None
    semantic_apply_gate_reason: str = (
        "No profile apply gate was computed for this candidate."
    )


@dataclass(frozen=True)
class ProfileInsightOpenReviewAction:
    review_lane: str
    route_group_key: str
    route_step_key: str
    semantic_move: str | None
    tool_name: str | None
    mcp_tool_name: str | None
    action_label: str | None
    arguments: dict[str, Any]
    suggested_next_call: str | None
    source_origin: str | None
    source_summary: dict[str, Any]
    target_detail: str | None


@dataclass(frozen=True)
class ProfileInsightOpenReviewLane:
    review_lane: str
    route_group_count: int
    route_group_keys: list[str]
    closed_route_step_keys: list[str]
    route_step_keys: list[str]
    closed_semantic_moves: list[str]
    remaining_semantic_moves: list[str]
    remaining_actions: list[ProfileInsightOpenReviewAction]
    action_count: int
    matched_candidate_revision_iris: list[str]
    matched_candidate_count: int
    next_step: str


@dataclass(frozen=True)
class ProfileInsightReviewBundleRecord:
    result_kind: str
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    profile_observation_iris: list[str]
    related_pattern_iris: list[str]
    candidate_revision_iris: list[str]
    candidate_count: int
    candidates: list[ProfileInsightReviewCandidate]
    open_profile_review_lanes: list[ProfileInsightOpenReviewLane]
    open_profile_review_lane_count: int
    closed_semantic_moves: list[str]
    remaining_semantic_moves: list[str]
    closed_route_step_keys: list[str]
    remaining_route_step_keys: list[str]
    semantic_move_closure_summary: str
    export: StagedGraphRevisionsExportRecord | None
    warnings: list[str]
    review_note: str
    profile_quality_summary: dict[str, Any] = field(default_factory=dict)
    sampled_evidence_caution: str | None = None
    artifact_kind: str = "profile_insight_review_bundle"
    importable: bool = False
    recommended_import_tool: str | None = None
    recovery_complete: bool = False
    semantic_apply_gate_summary: str = ""
    bulk_apply_allowed: bool = False
    safe_single_apply_candidate_revision_iris: list[str] = field(
        default_factory=list
    )
    semantic_apply_gate_counts: dict[str, int] = field(default_factory=dict)
    semantic_apply_gate_blocking_reasons: list[str] = field(default_factory=list)
    executor_decision_summary: dict[str, Any] = field(default_factory=dict)
    decision: str = "clean_by_scanner_only"
    scanner_clean: bool = True
    would_block_sensitive_export: bool = False
    sensitive_literal_count: int = 0
    privacy_warnings: list[str] = field(default_factory=list)
    shareability_review_required: bool = True
    shareability_review_status: str = "required_not_completed"
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class StagedGraphRevisionBatchRestageItem:
    source_revision_iri: str
    summary: str | None
    status_before: str
    decision_before: str
    routing_decision_before: str
    stale_resolution_state_before: str | None
    blocking_reasons_before: list[str]
    exact_drift_summary_before: list[StagedRevisionExactDriftSummary]
    source_staged_validation_status: str
    source_validation_result_count: int | None
    source_snapshot_evidence: RevisionSnapshotEvidenceStatus
    source_snapshot_evidence_completeness: str
    status_after: str
    decision_after: str
    routing_decision_after: str
    stale_resolution_state_after: str | None
    blocking_reasons_after: list[str]
    exact_drift_summary_after: list[StagedRevisionExactDriftSummary]
    current_staged_validation_status: str
    current_validation_result_count: int | None
    current_snapshot_evidence: RevisionSnapshotEvidenceStatus
    current_snapshot_evidence_completeness: str
    triples_to_add_after: int
    triples_to_remove_after: int
    action: str
    not_restageable_reason: str | None
    restaged_from: str | None
    restaged_revision_iri: str | None
    current_restaged_by: str | None
    current_revision_iri: str
    next_action_after: RevisionNextAction | None
    next_action_queue_item_after: RevisionNextActionQueueItem | None
    suggested_next_actions_after: list[SuggestedNextAction]
    repair_first_warning: str | None
    note: str


@dataclass(frozen=True)
class StagedGraphRevisionBatchRestageRecord:
    requested_revision_iris: list[str]
    processed_revision_iris: list[str]
    dry_run: bool
    would_restage_revision_iris: list[str]
    repair_first_revision_iris: list[str]
    repair_or_replace_source_revision_iris: list[str]
    restaged_revision_iris: list[str]
    skipped_revision_iris: list[str]
    already_handled_revision_iris: list[str]
    not_restageable_revision_iris: list[str]
    not_restageable_revision_iris_by_reason: dict[str, list[str]]
    restaged_revision_by_source: dict[str, str]
    current_revision_by_source: dict[str, str]
    review_revision_iris: list[str]
    items: list[StagedGraphRevisionBatchRestageItem]
    revision_summaries: list[StagedGraphRevisionExportSummary]
    bundle_summary: StagedGraphRevisionBundleSummary
    requires_recheck_after_each_apply: bool
    sequential_apply_recheck_candidate_iris: list[str]
    export_record: StagedGraphRevisionsExportRecord | None
    suggested_next_actions: list[SuggestedNextAction] = field(default_factory=list)
    suggested_next_calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StagedRevisionRecoveryLane:
    row_iri: str
    source_revision_iri: str
    current_revision_iri: str
    resolved_target_iri: str | None
    resolved_target_record_kind: str | None
    row_is_target: bool
    lane: str
    effective_recovery_action: str
    action_type: str | None
    action_label: str | None
    batch_action: str
    not_restageable_reason: str | None
    summary: str | None
    changed_graphs: list[str]
    shared_context_applies: bool
    shared_context_patch_count: int
    shared_context_graphs: list[str]
    status_before: str
    decision_before: str
    routing_decision_before: str
    stale_resolution_state_before: str | None
    blocking_reasons_before: list[str]
    exact_drift_summary: list[StagedRevisionExactDriftSummary]
    status_after: str
    decision_after: str
    routing_decision_after: str
    stale_resolution_state_after: str | None
    blocking_reasons_after: list[str]
    source_staged_validation_status: str
    source_validation_result_count: int | None
    current_staged_validation_status: str
    current_validation_result_count: int | None
    source_snapshot_evidence: RevisionSnapshotEvidenceStatus
    source_snapshot_evidence_completeness: str
    current_snapshot_evidence: RevisionSnapshotEvidenceStatus
    current_snapshot_evidence_completeness: str
    triples_to_add_after: int
    triples_to_remove_after: int
    restaged_from: str | None
    restaged_revision_iri: str | None
    current_restaged_by: str | None
    alternative_gate: StagedRevisionAlternativeGate | None
    next_action: RevisionNextAction | None
    next_action_queue_item: RevisionNextActionQueueItem | None
    repair_draft: StagedRevisionRebaseDraft | None
    repair_draft_error: str | None
    repair_draft_deferred_reason: str | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    batch_item: StagedGraphRevisionBatchRestageItem
    note: str


@dataclass(frozen=True)
class StagedRevisionResolvedTargetGroup:
    group_key: str
    queue: str
    action_type: str | None
    action_label: str | None
    resolved_target_iri: str | None
    resolved_target_record_kind: str | None
    lane_count: int
    row_iris: list[str]
    source_revision_iris: list[str]
    requested_revision_iris: list[str]
    current_revision_iris: list[str]
    latest_revision_iris: list[str]
    restage_chain_iris: list[str]
    applied_event_iris: list[str]
    row_is_target_all: bool
    row_is_target_any: bool
    semantic_risk_level: str | None
    semantic_risk_reasons: list[str]
    alternative_set_iris: list[str]
    alternative_set_source_iri: str | None
    alternative_set_roles: list[str]
    alternative_gate_statuses: list[str]
    alternative_applied_source_iris: list[str]
    alternative_applied_revision_iris: list[str]
    alternative_semantic_review_required: bool


@dataclass(frozen=True)
class StagedRevisionMutationFrontierItem:
    item_kind: str
    queue: str
    target_iri: str | None
    target_record_kind: str | None
    source_revision_iris: list[str]
    row_iris: list[str]
    action: SuggestedNextAction | RevisionNextAction | None
    call: str | None
    semantic_risk_level: str | None
    semantic_risk_reasons: list[str]
    alternative_set_iris: list[str]
    alternative_set_source_iri: str | None
    alternative_set_roles: list[str]
    alternative_gate_statuses: list[str]
    alternative_applied_source_iris: list[str]
    alternative_applied_revision_iris: list[str]
    requires_semantic_review_before_mutation: bool
    reason: str


@dataclass(frozen=True)
class StagedRevisionRecoveryUnattendedStep:
    step_kind: str
    label: str
    action: SuggestedNextAction | RevisionNextAction | None
    call: str | None
    can_run_now: bool
    prerequisite: str | None
    mutates: bool
    requires_replan_after_completion: bool
    stop_reason: str | None
    revision_iris: list[str]
    source_revision_iris: list[str]
    target_iris: list[str]
    note: str


@dataclass(frozen=True)
class StagedRevisionRecoveryPlan:
    result_kind: str
    helper: str
    mode: str
    selection_mode: str
    requested_revision_iris: list[str] | None
    processed_revision_iris: list[str]
    current_staged_work_only: bool
    include_drafts: bool
    repair_draft_limit: int | None
    repair_draft_attempted_count: int
    repair_drafts_included_count: int
    repair_drafts_deferred_count: int
    validation_scope: str | None
    drift_detail: str
    limit: int
    offset: int
    count: int
    returned_count: int
    total_count: int
    lanes: list[StagedRevisionRecoveryLane]
    lane_counts: dict[str, int]
    next_action_queue: dict[str, list[str]]
    next_action_queue_items: list[RevisionNextActionQueueItem]
    next_action_queue_item_counts: dict[str, int]
    resolved_target_groups: list[StagedRevisionResolvedTargetGroup]
    resolved_target_group_counts: dict[str, int]
    mutation_frontier_iris: list[str]
    mutation_frontier_items: list[StagedRevisionMutationFrontierItem]
    helper_mutation_frontier_actions: list[SuggestedNextAction]
    helper_mutation_frontier_calls: list[str]
    mutation_allowed_after: str
    first_mutation_action: SuggestedNextAction | RevisionNextAction | None
    first_mutation_call: str | None
    first_safe_review_or_mutation_action: (
        SuggestedNextAction | RevisionNextAction | None
    )
    first_safe_review_or_mutation_call: str | None
    first_safe_review_or_mutation_source: str | None
    blocking_preflight_actions: list[SuggestedNextAction]
    blocking_preflight_calls: list[str]
    recommended_unattended_steps: list[StagedRevisionRecoveryUnattendedStep]
    requires_recheck_after_each_apply: bool
    semantic_review_required_queue_counts: dict[str, int]
    would_restage_revision_iris: list[str]
    repair_first_revision_iris: list[str]
    repair_or_replace_source_revision_iris: list[str]
    not_restageable_revision_iris_by_reason: dict[str, list[str]]
    current_revision_by_source: dict[str, str]
    review_revision_iris: list[str]
    recommended_review_iris: list[str]
    recommended_mutation_review_iris: list[str]
    recommended_apply_or_restage_review_iris: list[str]
    recommended_repair_review_iris: list[str]
    recommended_applied_inspection_iris: list[str]
    sequential_apply_recheck_candidate_iris: list[str]
    revision_summaries: list[StagedGraphRevisionExportSummary]
    bundle_summary: StagedGraphRevisionBundleSummary | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    warnings: list[str]
    note: str


@dataclass(frozen=True)
class StagedRevisionRecoverySessionSourceState:
    source_revision_iri: str
    lane: str | None
    effective_recovery_action: str | None
    batch_action: str | None
    current_revision_iri: str | None
    resolved_target_iri: str | None
    resolved_target_record_kind: str | None
    next_action_queue: str | None
    next_action_tool_name: str | None
    applied_revision_iri: str | None
    current_staged_revision_iri: str | None
    latest_revision_iri: str | None
    latest_role: str | None
    restage_chain_iris: list[str]
    snapshot_status: str | None
    workflow_state: str


@dataclass(frozen=True)
class StagedRevisionRecoverySessionDescription:
    result_kind: str
    helper: str
    mode: str
    session_iri: str
    summary: str | None
    created_at: str | None
    created_by: str | None
    handoff_manifest_path: str | None
    source_revision_iris: list[str]
    source_count: int
    session_status: str
    current_staged_work_only: bool
    include_drafts: bool
    repair_draft_limit: int | None
    validation_scope: str | None
    drift_detail: str
    initial_selection_mode: str | None
    initial_lane_counts: dict[str, int]
    current_plan: StagedRevisionRecoveryPlan
    source_states: list[StagedRevisionRecoverySessionSourceState]
    completed_source_revision_iris: list[str]
    active_source_revision_iris: list[str]
    applied_event_iris: list[str]
    current_revision_by_source: dict[str, str]
    mutation_frontier_iris: list[str]
    helper_mutation_frontier_calls: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    warnings: list[str]
    note: str
    created_triples: int | None = None


@dataclass(frozen=True)
class _StagedRevisionApplicationPreview:
    staged: StagedGraphRevisionDescription
    check: StagedRevisionApplyCheck
    parsed_patches: list[tuple[StagedGraphPatchDescription, Graph]]
    preview_graphs: dict[str, Graph]


@dataclass(frozen=True)
class _StagedRevisionDriftTerms:
    patch_subjects: set[str]
    patch_predicates: set[str]
    patch_objects: set[str]
    revision_anchors: set[str]


@dataclass
class _ChangedGraphResourceAccumulator:
    iri: str
    added_triple_count: int = 0
    removed_triple_count: int = 0
    matched_by: set[str] = field(default_factory=set)
    predicate_iris: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class GraphSnapshotDescription:
    graph_role: str
    triple_count: int
    content_digest: str | None


@dataclass(frozen=True)
class RevisionSnapshotEvidenceStatus:
    revision_iri: str
    status: str
    history_revision_found: bool
    rdf_snapshot_graph_roles: list[str]
    stored_snapshot_graph_roles: list[str]
    exact_snapshot_graph_roles: list[str]
    missing_snapshot_row_graph_roles: list[str]
    orphan_snapshot_row_graph_roles: list[str]
    missing_current_graph_roles: list[str]
    note: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class RevisionGraphSnapshotDescription:
    revision_iri: str
    graph_role: str
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    triple_count: int | None
    content_digest: str | None
    count_basis: str
    stored_at: str | None
    exact_snapshot_available: bool
    include_triples: bool
    triples_included: bool
    triples_truncated: bool
    max_triples: int
    triples: list[GraphTripleDescription]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    note: str


@dataclass(frozen=True)
class StagedGraphPatchDescription:
    iri: str
    operation: str
    operation_label: str | None
    target_graph: str | None
    count_basis: str | None
    format: str | None
    patch_role: str | None
    patch_role_label: str | None
    sequence_index: int | None
    triple_count: int | None
    before_triple_count: int | None
    after_triple_count: int | None
    content: str | None


@dataclass(frozen=True)
class StagedRevisionImpactValue:
    value: str
    value_label: str | None
    value_kind: str
    caveat: CaveatDescription | None = None


@dataclass(frozen=True)
class StagedRevisionImpact:
    impact_type: str
    severity: str
    changed_graph: str | None
    subject: ResourceSummary | None
    predicate: str | None
    predicate_label: str | None
    message: str
    removed_values: list[StagedRevisionImpactValue]
    added_values: list[StagedRevisionImpactValue]
    related_observations: list[ResourceSummary]
    related_claims: list[ResourceSummary]
    related_patterns: list[ResourceSummary]
    related_evidence: list[ResourceSummary]
    related_revisions: list[ResourceSummary]
    related_context_note: str | None


@dataclass(frozen=True)
class StagedRevisionStoredReviewNoteSignals:
    has_value_type_context: bool
    has_current_value_rationale: bool
    has_caveat_context: bool
    has_related_routes: bool
    has_user_review_note: bool


@dataclass(frozen=True)
class StagedRevisionStoredReviewSupportCounts:
    observations: int
    claims: int
    patterns: int
    evidence: int
    revision_anchors: int


@dataclass(frozen=True)
class StagedRevisionStoredReviewContext:
    source_fields: list[str]
    semantic_risk_level: str
    semantic_risk_reasons: list[str]
    review_recommendation: str | None
    review_note_signals: StagedRevisionStoredReviewNoteSignals
    linked_support_counts: StagedRevisionStoredReviewSupportCounts
    attention_impacts: list[StagedRevisionImpact]


@dataclass(frozen=True)
class AppliedStagedRevisionSourcePatchSummary:
    operation: str | None
    operation_label: str | None
    target_graph: str | None
    count_basis: str | None
    patch_role: str | None
    patch_role_label: str | None
    sequence_index: int | None
    triple_count: int | None
    before_triple_count: int | None
    after_triple_count: int | None


@dataclass(frozen=True)
class AppliedStagedRevisionSourceSummary:
    iri: str
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    revision_stance: str | None
    revision_stance_label: str | None
    review_note: str | None
    review_recommendation: str | None
    alternative_to: str | None
    restaged_from: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    restage_reason: str | None
    created_at: str | None
    created_by: str | None
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    changed_graphs: list[str]
    included_graphs: list[str]
    graph_snapshots: list[GraphSnapshotDescription]
    patch_count: int
    patches: list[AppliedStagedRevisionSourcePatchSummary]
    supporting_observation_count: int
    supporting_claim_count: int
    supporting_pattern_count: int
    evidence_count: int
    revision_anchor_count: int


@dataclass(frozen=True)
class GraphRevisionDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    record_kind: str
    revision_type: str | None
    revision_type_label: str | None
    rationale: str | None
    changed_graphs: list[str]
    included_graphs: list[str]
    created_at: str | None
    created_by: str | None
    export_path: str | None
    applies_staged_revision: str | None
    resolves_staged_revision: str | None
    staged_review_decision: str | None
    staged_review_decision_label: str | None
    applied_source: AppliedStagedRevisionSourceSummary | None
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    graph_snapshots: list[GraphSnapshotDescription]
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ResourceSummary]
    supporting_patterns: list[ResourceSummary]
    revision_anchors: list[ResourceSummary]
    evidence: list[ResourceSummary]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class GraphRevisionListItem:
    iri: str
    record_kind: str
    is_current_staged_work: bool
    not_current_staged_work_reason: str | None
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    revision_stance: str | None
    revision_stance_label: str | None
    created_at: str | None
    changed_graphs: list[str]
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    staged_validation_status: str
    has_patch_payload: bool
    patch_count: int
    applied_by: str | None
    applies_staged_revision: str | None
    alternative_to: str | None
    current_alternative_to: str | None
    alternative_gate: StagedRevisionAlternativeGate
    restaged_from: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    review_resolution: StagedRevisionReviewResolutionSummary | None
    stale_resolution_state: str | None
    application_status: str | None
    application_decision: str | None
    application_can_apply: bool | None
    application_summary: str | None
    application_recommended_resolution: str | None
    application_validation_skipped_reason: str | None
    application_blocking_reasons: list[str]
    application_count_drifts: list[StagedGraphCountDrift]
    application_snapshot_drifts: list[StagedGraphSnapshotDrift]
    application_semantic_risk_level: str | None
    application_semantic_risk_reasons: list[str]
    profile_route_keys: list[str]
    profile_route_groups: list[dict[str, Any]]
    profile_gate_label: str | None
    profile_generic_queue_caution: str | None
    profile_semantic_apply_role: str | None
    profile_apply_cardinality: str | None
    profile_safe_single_apply_candidate: bool | None
    profile_bulk_apply_allowed: bool | None
    profile_semantic_apply_gate_reason: str | None
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    next_action: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class GraphRevisionList:
    revisions: list[GraphRevisionListItem]
    count: int
    returned_count: int
    total_count: int
    limit: int
    offset: int
    revision_type: str | None
    record_kind: str | None
    application_status: str | None
    staged_validation_status: str | None
    stale_resolution_state: str | None
    current_staged_work_only: bool
    returned_application_status_counts: dict[str, int]
    returned_current_staged_work_application_status_counts: dict[str, int]
    returned_stale_resolution_state_counts: dict[str, int]
    returned_staged_validation_status_counts: dict[str, int]
    next_action_queue: dict[str, list[str]]
    next_action_queue_items: list[RevisionNextActionQueueItem]
    next_action_queue_item_counts: dict[str, int]
    semantic_review_required_queue_counts: dict[str, int]
    include_apply_checks: bool
    drift_detail: str


@dataclass(frozen=True)
class GraphVersionListItem:
    revision_iri: str
    graph_role: str
    record_kind: str
    snapshot_semantics: str
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    created_at: str | None
    changed_graphs: list[str]
    included_graphs: list[str]
    applies_staged_revision: str | None
    applied_by: str | None
    restaged_from: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    is_current_staged_work: bool
    not_current_staged_work_reason: str | None
    review_resolution: StagedRevisionReviewResolutionSummary | None
    staged_validation_status: str
    stale_resolution_state: str | None
    application_status: str | None
    application_decision: str | None
    application_can_apply: bool | None
    application_blocking_reasons: list[str]
    alternative_gate_status: str | None
    alternative_semantic_review_required: bool
    alternative_applied_source_iri: str | None
    alternative_applied_revision_iri: str | None
    triple_count: int | None
    content_digest: str | None
    count_basis: str
    stored_at: str | None
    exact_snapshot_available: bool
    snapshot_evidence_status: str
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    next_action: RevisionNextAction | None
    next_action_queue_item: RevisionNextActionQueueItem | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class GraphVersionList:
    graph_role: str
    graph: str | None
    exact_only: bool
    include_current: bool
    include_apply_checks: bool
    drift_detail: str
    record_kind: str | None
    limit: int
    offset: int
    count: int
    total_count: int
    returned_count: int
    current_graph: GraphSnapshotDescription | None
    snapshot_evidence_status_counts: dict[str, int]
    exact_snapshot_available_count: int
    versions: list[GraphVersionListItem]
    note: str


@dataclass(frozen=True)
class GraphVersionRevisionContext:
    revision_iri: str
    record_kind: str
    snapshot_semantics: str
    summary: str | None
    application_status: str | None
    application_decision: str | None
    staged_validation_status: str
    is_current_staged_work: bool
    not_current_staged_work_reason: str | None
    review_resolution: StagedRevisionReviewResolutionSummary | None
    applies_staged_revision: str | None
    applied_by: str | None
    restaged_from: str | None
    restaged_by: str | None
    current_restaged_by: str | None
    alternative_gate_status: str | None
    alternative_semantic_review_required: bool
    alternative_applied_source_iri: str | None
    alternative_applied_revision_iri: str | None
    related_revision_iris: list[str]


@dataclass(frozen=True)
class GraphVersionDiffDescription:
    graph_role: str
    graph: str | None
    before_revision_iri: str
    after_revision_iri: str | None
    compare_to_current: bool
    after_target_kind: str
    before_revision_context: GraphVersionRevisionContext | None
    after_revision_context: GraphVersionRevisionContext | None
    related_revision_iris: list[str]
    before_snapshot: RevisionGraphSnapshotDescription
    after_snapshot: RevisionGraphSnapshotDescription | None
    current_graph: GraphSnapshotDescription | None
    count_basis: str
    before_triple_count: int | None
    after_triple_count: int | None
    count_delta: int | None
    before_content_digest: str | None
    after_content_digest: str | None
    digest_changed: bool | None
    exact_changed_triples_available: bool
    exact_changed_triples_included: bool
    triples_added_count: int | None
    triples_removed_count: int | None
    triples_added_truncated: bool
    triples_removed_truncated: bool
    max_triples: int
    changed_resource_count: int | None
    changed_resources_returned_count: int
    changed_resources_omitted_count: int | None
    changed_resources: list[ChangedGraphResourceSummary]
    changed_resource_suggested_next_actions: list[SuggestedNextAction]
    triples_added: list[GraphTripleDescription]
    triples_removed: list[GraphTripleDescription]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    note: str


@dataclass(frozen=True)
class RevisionLineageDescription:
    selected_revision: GraphRevisionListItem
    selected_revision_iri: str
    selected_role: str
    paired_revision: GraphRevisionListItem | None
    paired_revision_iri: str | None
    paired_role: str | None
    applied_revision_iri: str | None
    staged_revision_iri: str | None
    applied_source_revision_iri: str | None
    current_staged_revision_iri: str | None
    current_revision_iri: str | None
    latest_revision_iri: str | None
    latest_role: str | None
    restage_chain: list[GraphRevisionListItem]
    restage_chain_iris: list[str]
    alternative_revision_iris: list[str]
    related_revision_iris: list[str]
    next_action: RevisionNextAction | None
    next_action_queue_item: RevisionNextActionQueueItem | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    warnings: list[str]
    include_apply_checks: bool
    drift_detail: str


@dataclass(frozen=True)
class ResourceRevisionPatchMention:
    patch_iri: str
    target_graph: str | None
    operation: str | None
    operation_label: str | None
    patch_role: str | None
    patch_role_label: str | None
    sequence_index: int | None
    matched_term_roles: list[str]
    matched_triples: int
    triple_count: int | None


@dataclass(frozen=True)
class _ResourceRevisionPatchMentionScan:
    mentions: list[ResourceRevisionPatchMention]
    unreadable_patch_count: int
    unreadable_patch_iris: list[str]


@dataclass(frozen=True)
class ResourceRevisionPatchMentionScanSummary:
    status: str
    unreadable_patch_count: int
    unreadable_revision_count: int
    omitted_match_risk: bool


@dataclass(frozen=True)
class ResourceRevisionListItem:
    revision: GraphRevisionListItem
    revision_iri: str
    match_types: list[str]
    revision_anchor_match: bool
    patch_mention_match: bool
    applied_source_match: bool
    applied_source_revision_iri: str | None
    patch_mentions: list[ResourceRevisionPatchMention]
    patch_mentions_incomplete: bool
    patch_mentions_unreadable_count: int
    applied_source_patch_mentions: list[ResourceRevisionPatchMention]
    applied_source_patch_mentions_incomplete: bool
    applied_source_patch_mentions_unreadable_count: int


@dataclass(frozen=True)
class ResourceRevisionTimelineEvent:
    event_index: int
    revision_iri: str
    record_kind: str
    timeline_role: str
    summary: str | None
    created_at: str | None
    changed_graphs: list[str]
    match_types: list[str]
    application_status: str | None
    stale_resolution_state: str | None
    not_current_staged_work_reason: str | None
    applied_revision_iri: str | None
    staged_revision_iri: str | None
    applied_by: str | None
    applied_source_revision_iri: str | None
    restaged_from: str | None
    current_restaged_by: str | None
    queue: str | None
    action_type: str | None
    resolved_target_iri: str | None
    resolved_target_record_kind: str | None
    row_is_target: bool | None
    next_action_call: str | None


@dataclass(frozen=True)
class ResourceRevisionList:
    resource: ResourceSummary
    revisions: list[ResourceRevisionListItem]
    timeline: list[ResourceRevisionTimelineEvent]
    timeline_note: str
    count: int
    returned_count: int
    total_count: int
    limit: int
    offset: int
    current_staged_work_only: bool
    include_patch_mentions: bool
    patch_mention_scan: ResourceRevisionPatchMentionScanSummary
    include_apply_checks: bool
    drift_detail: str
    next_action_queue: dict[str, list[str]]
    next_action_queue_items: list[RevisionNextActionQueueItem]
    next_action_queue_item_counts: dict[str, int]
    semantic_review_required_queue_counts: dict[str, int]


@dataclass(frozen=True)
class ResourceAppliedRevisionGraphDiffSummary:
    graph_role: str
    count_basis: str
    before_revision_iri: str
    after_revision_iri: str
    before_triple_count: int | None
    after_triple_count: int | None
    before_content_digest: str | None
    after_content_digest: str | None
    exact_changed_triples_available: bool
    exact_changed_triples_included: bool
    resource_triples_added_count: int | None
    resource_triples_removed_count: int | None
    resource_triples_added_truncated: bool
    resource_triples_removed_truncated: bool
    max_triples: int
    resource_triples_added: list[GraphTripleDescription]
    resource_triples_removed: list[GraphTripleDescription]
    note: str


@dataclass(frozen=True)
class ResourceAppliedRevisionDiffSummary:
    applied_revision_iri: str
    staged_revision_iri: str
    snapshot_evidence: RevisionSnapshotEvidenceStatus
    source_snapshot_evidence: RevisionSnapshotEvidenceStatus
    changed_graphs: list[str]
    include_triples: bool
    max_triples: int
    graph_diffs: list[ResourceAppliedRevisionGraphDiffSummary]


@dataclass(frozen=True)
class ResourceRevisionLineageDescription:
    resource: ResourceSummary
    selected_revision: ResourceRevisionListItem
    selected_revision_iri: str
    selected_role: str
    paired_revision: ResourceRevisionListItem | None
    paired_revision_iri: str | None
    paired_role: str | None
    applied_revision_iri: str | None
    staged_revision_iri: str | None
    applied_source_revision_iri: str | None
    current_staged_revision_iri: str | None
    current_revision_iri: str | None
    latest_revision_iri: str | None
    latest_role: str | None
    restage_chain_iris: list[str]
    alternative_revision_iris: list[str]
    related_revision_iris: list[str]
    warnings: list[str]
    patch_mention_scan: ResourceRevisionPatchMentionScanSummary
    next_action: RevisionNextAction | None
    next_action_queue_item: RevisionNextActionQueueItem | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    applied_diff_status: str
    applied_diff_note: str | None
    applied_diff: ResourceAppliedRevisionDiffSummary | None


@dataclass(frozen=True)
class StagedGraphRevisionDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    revision_stance: str | None
    revision_stance_label: str | None
    rationale: str | None
    review_note: str | None
    review_recommendation: str | None
    alternative_to: ResourceSummary | None
    alternative_gate: StagedRevisionAlternativeGate
    restaged_from: ResourceSummary | None
    restaged_by: ResourceSummary | None
    current_restaged_by: ResourceSummary | None
    applied_by: ResourceSummary | None
    review_resolution: StagedRevisionReviewResolutionSummary | None
    application_status: str | None
    restage_reason: str | None
    changed_graphs: list[str]
    included_graphs: list[str]
    created_at: str | None
    created_by: str | None
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    graph_snapshots: list[GraphSnapshotDescription]
    patches: list[StagedGraphPatchDescription]
    impacts: list[StagedRevisionImpact]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ResourceSummary]
    supporting_patterns: list[ResourceSummary]
    revision_anchors: list[ResourceSummary]
    evidence: list[ResourceSummary]
    profile_route_sources: list[dict[str, Any]]
    profile_route_keys: list[str]
    profile_route_groups: list[dict[str, Any]]
    current_apply_check: StagedRevisionApplySummary | None = None
    judgement_panel: MapAssertionJudgementPanel | None = None
    stored_review_context: StagedRevisionStoredReviewContext | None = None


@dataclass(frozen=True)
class EntityRow:
    iri: str
    label: str | None
    types: list[str]
    graph: str


@dataclass(frozen=True)
class EntityList:
    entities: list[EntityRow]
    limit: int
    offset: int
    returned_count: int
    total_count: int
    omitted_count: int
    has_more: bool
    next_offset: int | None
    suggested_next_actions: list[SuggestedNextAction] = field(default_factory=list)
    suggested_next_calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResourceSummary:
    iri: str
    label: str | None
    description: str | None
    column_name: str | None = None
    owning_dataset_iri: str | None = None
    owning_dataset_label: str | None = None


@dataclass(frozen=True)
class ObservedValueFrequencySummary:
    iri: str
    value: str
    frequency: int


@dataclass(frozen=True)
class ObservedProfileMetricSummary:
    iri: str
    metric: ResourceSummary
    target: ResourceSummary | None
    value: str
    value_datatype: str | None
    value_lang: str | None


@dataclass(frozen=True)
class ProfileObservationSummary:
    iri: str
    summary: str | None
    observed_at: str | None
    observed_by: str | None
    observed_asset: ResourceSummary | None
    observed_column: ResourceSummary | None
    observed_column_name: str | None
    observed_physical_type: ResourceSummary | None
    observed_value_type: ResourceSummary | None
    sample_size: int | None
    sample_scope: str | None
    sample_method: str | None
    row_count: int | None
    null_count: int | None
    distinct_count: int | None
    value_frequencies: list[ObservedValueFrequencySummary]
    profile_metrics: list[ObservedProfileMetricSummary]
    evidence: list[EvidenceDescription]


@dataclass(frozen=True)
class ColumnDescription:
    iri: str
    label: str | None
    description: str | None
    column_name: str | None
    physical_type: ResourceSummary | None
    value_type: ResourceSummary | None
    nullable: bool | None
    profile_observations: list[ProfileObservationSummary]


@dataclass(frozen=True)
class PhysicalLayoutDescription:
    iri: str
    label: str | None
    description: str | None
    file_format: ResourceSummary | None
    compression_codec: ResourceSummary | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class StorageAccessDescription:
    iri: str
    label: str | None
    description: str | None
    route_roles: list[ResourceSummary]
    storage_protocol: ResourceSummary | None
    access_mode: ResourceSummary | None
    location_kind: str | None
    storage_root: str | None
    endpoint_profile: str | None
    bucket_name: str | None
    key_prefix: str | None
    region: str | None
    path_style_access: bool | None
    credential_reference: str | None
    path_templates: list[str]
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class PartitionDescription:
    iri: str
    label: str | None
    description: str | None
    partition_column: ResourceSummary | None
    partition_columns: list[ResourceSummary]
    granularity: ResourceSummary | None
    path_template: str | None
    redundant_partition_key: ResourceSummary | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class QueryPlanningIssue:
    code: str
    severity: str
    message: str
    domain: str = "query_planning"
    resource: ResourceSummary | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class QueryRepairActionGroup:
    group_name: str
    issue_index: int
    issue_code: str
    issue_severity: str
    issue_message: str
    issue_resource: ResourceSummary | None
    repair_hint_path: str
    repair_action_type: str | None
    requires_review: bool
    repair_context: dict[str, Any]
    choice_mode: str
    actions: list[dict[str, Any]]
    action_count: int
    action_status_counts: dict[str, int]
    pending_action_count: int
    skippable_action_count: int
    already_satisfied_action_count: int
    pending_required_extra_arguments: list[str]
    pending_action_options: list[dict[str, Any]]
    group_advisories: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class QueryTargetCandidate:
    candidate_selector: str
    template: str
    template_source: str
    source_resource: ResourceSummary
    storage_access: ResourceSummary | None
    route_roles: list[ResourceSummary]
    storage_protocol: ResourceSummary | None
    access_mode: ResourceSummary | None
    location_kind: str | None
    storage_root: str | None
    endpoint_profile: str | None
    bucket_name: str | None
    key_prefix: str | None
    region: str | None
    candidate_path: str | None
    relation_identifier: str | None
    connection_reference: str | None
    composition: str
    candidate_path_status: str
    requires_endpoint_profile: bool
    credential_reference: str | None
    path_style_access: bool | None
    review_required: bool
    review_reasons: list[QueryPlanningIssue]
    direct_review_required: bool
    direct_review_reasons: list[QueryPlanningIssue]
    required_bindings: list[str] = field(default_factory=list)
    required_binding_details: list[dict[str, Any]] = field(default_factory=list)
    binding_example: str | None = None
    binding_examples: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class QueryTargetDecision:
    status: str
    summary: str
    candidate_index: int | None
    candidate_path: str | None
    candidate_path_status: str | None
    direct_review_required: bool | None
    selected_candidate_direct_clean: bool | None
    reason_codes: list[str]
    selection_reason_codes: list[str] = field(default_factory=list)
    peer_ready_requires_intent_review: bool = False
    selection_caution: str | None = None
    route_intent_review_candidate_indexes: list[int] = field(default_factory=list)
    route_intent_caution: str | None = None


@dataclass(frozen=True)
class QueryPlanningContext:
    dataset: ResourceSummary
    readiness: str
    readiness_note: str
    issues: list[QueryPlanningIssue]
    analysis_warnings: list[QueryPlanningIssue]
    suggested_repair_action_groups: list[QueryRepairActionGroup]
    suggested_repair_action_group_count: int
    planning_notes: list[str]
    row_count_snapshot: int | None
    profile_summary: ProfileSummary
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None
    columns: list[ColumnDescription]
    path_templates: list[str]
    query_target_decision: QueryTargetDecision
    query_target_candidates: list[QueryTargetCandidate]
    ready_candidate_indexes: list[int]
    unselected_ready_candidate_indexes: list[int]
    direct_clean_candidate_indexes: list[int]
    unselected_direct_clean_candidate_indexes: list[int]
    physical_layouts: list[PhysicalLayoutDescription]
    storage_accesses: list[StorageAccessDescription]
    partition_schemes: list[PartitionDescription]
    caveats: list[CaveatDescription]
    upstream_caveats: list[CaveatDescription]
    suggested_next_actions: list[SuggestedNextAction]
    safe_inspection_action_indexes: list[int]
    first_safe_inspection_action_index: int | None
    unattended_recommended_action_indexes: list[int]
    first_unattended_action_index: int | None
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class DraftQueryPlanEngine:
    name: str
    source: str


@dataclass(frozen=True)
class DraftQueryPlanSourceContext:
    api: str
    readiness: str
    readiness_note: str
    query_target_decision: QueryTargetDecision
    selected_candidate_index: int | None
    candidate_count: int = 0
    ready_candidate_indexes: list[int] = field(default_factory=list)
    unselected_ready_candidate_indexes: list[int] = field(default_factory=list)
    direct_clean_candidate_indexes: list[int] = field(default_factory=list)
    unselected_direct_clean_candidate_indexes: list[int] = field(
        default_factory=list
    )
    selection_mode: str = "automatic"
    requested_candidate_index: int | None = None
    requested_candidate_selector: str | None = None
    requested_storage_access_iri: str | None = None
    requested_physical_layout_iri: str | None = None
    selected_candidate_selector: str | None = None
    selection_status: str = "automatic"
    selection_note: str = ""
    selected_candidate_note: str = ""
    allow_context_blocked_candidate: bool = False
    selection_reason_codes: list[str] = field(default_factory=list)
    peer_ready_requires_intent_review: bool = False
    selection_caution: str | None = None
    route_intent_review_candidate_indexes: list[int] = field(default_factory=list)
    route_intent_caution: str | None = None


@dataclass(frozen=True)
class DraftQueryPlanScan:
    function: str | None
    uri_template: str | None
    relation_identifier: str | None
    connection_reference: str | None
    file_format: str | None
    compression: str | None
    candidate_path_status: str | None
    dataset_verification_status: ResourceSummary | None
    dataset_verification_note: str | None
    template: str | None
    template_source: str | None
    template_source_resource: ResourceSummary | None
    template_source_verification_status: ResourceSummary | None
    template_source_verification_note: str | None
    template_lineage: str | None
    composition: str | None
    physical_layout: ResourceSummary | None
    physical_layout_selection_note: str | None
    non_executed_note: str
    execution_attempt_ready: bool = False
    primary_execution_attempt_blocking_reason_code: str | None = None
    execution_attempt_blocking_reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftQueryPlanBindingColumnMatch:
    column: ResourceSummary
    match_kind: str
    matched_field: str
    matched_value: str
    confidence: str


@dataclass(frozen=True)
class DraftQueryPlanBinding:
    name: str
    source: str
    source_text: str | None
    required: bool
    derivation_status: str
    derivation_note: str
    binding_kind: str = "path_template_placeholder"
    partition_scheme: ResourceSummary | None = None
    partition_column: ResourceSummary | None = None
    partition_granularity: ResourceSummary | None = None
    candidate_column_matches: list[DraftQueryPlanBindingColumnMatch] = field(
        default_factory=list
    )
    candidate_column_match_status: str = "not_applicable"


@dataclass(frozen=True)
class DraftQueryPlanStorageEnvironment:
    storage_protocol: ResourceSummary | None
    storage_root: str | None
    bucket_name: str | None
    key_prefix: str | None
    region: str | None
    endpoint_profile: str | None
    credential_reference: str | None
    access_mode: ResourceSummary | None
    path_style_access: bool | None
    requires_endpoint_profile: bool
    runtime_resolution_required: bool
    duckdb_settings_from_context: list[str]
    runtime_resolution_note: str


@dataclass(frozen=True)
class DraftQueryPlanReviewGate:
    executable_without_review: bool
    runtime_resolution_required: bool
    binding_values_required: bool
    ready_for_execution_attempt: bool
    status: str
    direct_review_required: bool | None
    candidate_path_status: str | None
    blocking_reason_codes: list[str]
    execution_attempt_blocking_reason_codes: list[str]
    primary_execution_attempt_blocking_reason_code: str | None
    all_issue_codes: list[str]
    reason_codes: list[str]
    review_note: str
    selection_overridden: bool = False
    context_blocked_candidate_allowed: bool = False
    context_blocked_candidate_used: bool = False
    direct_blocking_reason_codes: list[str] = field(default_factory=list)
    context_blocking_reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftQueryPlanHandoffSummary:
    handoff_kind: str
    selected_candidate_index: int | None
    selected_candidate_selector: str | None
    selected_candidate_note: str
    scan_function: str | None
    uri_template: str | None
    relation_identifier: str | None
    connection_reference: str | None
    candidate_path_status: str | None
    executable_without_review: bool
    ready_for_execution_attempt: bool
    primary_execution_attempt_blocking_reason_code: str | None
    execution_attempt_blocking_reason_codes: list[str]
    runtime_resolution_required: bool
    binding_values_required: bool
    required_bindings: list[str]
    all_issue_codes: list[str]
    context_blocked_candidate_allowed: bool
    context_blocked_candidate_used: bool
    direct_blocking_reason_codes: list[str]
    context_blocking_reason_codes: list[str]
    analysis_warning_count: int
    caveat_count: int
    unselected_ready_candidate_indexes: list[int]
    unselected_direct_clean_candidate_indexes: list[int]
    selection_reason_codes: list[str]
    peer_ready_requires_intent_review: bool
    selection_caution: str | None
    route_intent_review_candidate_indexes: list[int] = field(default_factory=list)
    route_intent_caution: str | None = None
    primary_repair_issue_index: int | None = None
    primary_repair_issue_code: str | None = None
    primary_repair_group_action_type: str | None = None
    primary_repair_action_index: int | None = None
    primary_repair_action_type: str | None = None
    primary_repair_action_label: str | None = None
    primary_repair_tool_name: str | None = None
    primary_repair_mcp_tool_name: str | None = None
    primary_repair_required_extra_arguments: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftQueryPlan:
    helper: str
    mode: str
    handoff_kind: str
    handoff_summary: DraftQueryPlanHandoffSummary
    engine: DraftQueryPlanEngine
    dataset: ResourceSummary
    source_context: DraftQueryPlanSourceContext
    selected_candidate: QueryTargetCandidate | None
    scan: DraftQueryPlanScan
    required_bindings: list[str]
    binding_requirements: list[DraftQueryPlanBinding]
    binding_note: str
    storage_environment: DraftQueryPlanStorageEnvironment
    review_gate: DraftQueryPlanReviewGate
    issues: list[QueryPlanningIssue]
    analysis_warnings: list[QueryPlanningIssue]
    caveats: list[CaveatDescription]
    upstream_caveats: list[CaveatDescription]
    planning_notes: list[str]


@dataclass(frozen=True)
class RelatedDatasetDescription:
    iri: str
    label: str | None
    description: str | None
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None


@dataclass(frozen=True)
class RelatedDatasetReasonTag:
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None
    declared: bool | None
    referential_integrity: ResourceSummary | None


@dataclass(frozen=True)
class RelatedDatasetReason:
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None
    columns: list[ResourceSummary]
    current_dataset_columns: list[ResourceSummary]
    related_dataset_columns: list[ResourceSummary]
    declared: bool | None
    referential_integrity: ResourceSummary | None
    source_caveats: list[CaveatDescription]
    relationship_tags: list[RelatedDatasetReasonTag]


@dataclass(frozen=True)
class RelatedDatasetGroup:
    iri: str
    label: str | None
    description: str | None
    reasons: list[RelatedDatasetReason]


@dataclass(frozen=True)
class LinkedPatternMatch:
    match_type: str
    matched_resource: ResourceSummary
    supporting_claim: ResourceSummary | None
    supporting_observation: ResourceSummary | None


@dataclass(frozen=True)
class LinkedPatternMatchGroup:
    matched_resource: ResourceSummary
    matched_resource_types: list[str]
    matched_resource_kind: str | None
    relevance_tier: str
    route_types: list[str]
    route_labels: list[str]
    supporting_claims: list[ResourceSummary]
    supporting_observations: list[ResourceSummary]


@dataclass(frozen=True)
class LinkedPatternReason:
    iri: str
    pattern_iri: str
    label: str | None
    pattern_text: str | None
    rationale: str | None
    match_group_count: int
    raw_match_count: int
    relevance_tier_counts: dict[str, int]
    match_groups: list[LinkedPatternMatchGroup]
    matches: list[LinkedPatternMatch]


@dataclass(frozen=True)
class CaveatDescription:
    iri: str
    label: str | None
    description: str | None
    impact: str | None
    severity: ResourceSummary | None


@dataclass(frozen=True)
class AssertionSupportCaveatLink:
    caveat: CaveatDescription
    scope: str
    route_type: str
    route_label: str
    via_resource: ResourceSummary
    matched_resource: ResourceSummary


@dataclass(frozen=True)
class TransformationDescription:
    iri: str
    label: str | None
    description: str | None
    transformation_type: str | None
    transformation_description: str | None


@dataclass(frozen=True)
class AnalysisDenominatorDescription:
    iri: str
    label: str | None
    description: str | None
    row_count_snapshot: int | None
    basis: str | None


@dataclass(frozen=True)
class QuerySnippetDescription:
    iri: str
    label: str | None
    description: str | None
    query_text: str | None
    query_language: str | None
    query_engine: str | None


@dataclass(frozen=True)
class AnalysisViewDescription:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    source_datasets: list[ResourceSummary]
    denominator: AnalysisDenominatorDescription | None
    query_snippets: list[QuerySnippetDescription]
    caveats: list[CaveatDescription]
    source_caveats: list[CaveatDescription]
    row_count_snapshot: int | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class AnalysisViewBundleRecord:
    records: list[MapResourceRecord]
    analysis_views: list[AnalysisViewDescription]
    view_iris: list[str]
    view_count: int
    query_snippet_count: int
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class AnalysisArtifactRecord:
    iri: str
    graph: str
    triples: int


@dataclass(frozen=True)
class AnalysisQueryRecipeRecord:
    iri: str
    graph: str
    triples: int


@dataclass(frozen=True)
class AnalysisFollowupTaskRecord:
    iri: str
    graph: str
    triples: int


@dataclass(frozen=True)
class AnalysisPacketRecord:
    packet_iri: str
    evidence_iri: str
    graph: str
    packet_triples: int
    analysis_view_bundle: AnalysisViewBundleRecord | None
    analysis_view_iris: list[str]
    artifact_records: list[AnalysisArtifactRecord]
    artifact_iris: list[str]
    query_recipe_records: list[AnalysisQueryRecipeRecord]
    query_recipe_iris: list[str]
    followup_task_records: list[AnalysisFollowupTaskRecord]
    followup_task_iris: list[str]
    pattern: PatternRecord | None
    pattern_iri: str | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class AggregatedColumnDescription:
    iri: str
    target_column: ResourceSummary | None
    source_columns: list[ResourceSummary]
    aggregation_function: ResourceSummary | None
    within_group_ordering: ResourceSummary | None


@dataclass(frozen=True)
class RelationshipEndpointDescription:
    iri: str
    dataset: ResourceSummary | None
    direction: str | None
    direction_label: str | None
    role: str | None
    order: int | None


@dataclass(frozen=True)
class TransformConditionDescription:
    iri: str
    label: str | None
    description: str | None
    condition_kind: ResourceSummary | None
    expression: str | None
    expression_language: str | None
    applies_to_datasets: list[ResourceSummary]
    applies_to_endpoints: list[ResourceSummary]


@dataclass(frozen=True)
class GrainComponentDescription:
    iri: str
    label: str | None
    description: str | None
    order: int | None
    role: str | None
    column: ResourceSummary | None
    dataset: ResourceSummary | None
    expression: str | None


@dataclass(frozen=True)
class TupleGrainDescription:
    iri: str
    label: str | None
    description: str | None
    components: list[GrainComponentDescription]


@dataclass(frozen=True)
class TransformOutputDescription:
    iri: str
    label: str | None
    description: str | None
    target_dataset: ResourceSummary | None
    role: str | None
    formula: str | None
    expression_language: str | None
    function: ResourceSummary | None
    conditions: list[TransformConditionDescription]
    tuple_grain: TupleGrainDescription | None


@dataclass(frozen=True)
class RelationshipDescription:
    iri: str
    label: str | None
    description: str | None
    types: list[str]
    relationship_kind: str | None
    relationship_kind_label: str | None
    relationship_type: str | None
    source_dataset: ResourceSummary | None
    target_dataset: ResourceSummary | None
    source_datasets: list[ResourceSummary]
    target_datasets: list[ResourceSummary]
    endpoints: list[RelationshipEndpointDescription]
    source_endpoints: list[RelationshipEndpointDescription]
    target_endpoints: list[RelationshipEndpointDescription]
    foreign_key_from: ResourceSummary | None
    foreign_key_to: ResourceSummary | None
    referential_integrity: ResourceSummary | None
    declared: bool | None
    identifying_columns: list[ResourceSummary]
    source_columns: list[ResourceSummary]
    derived_columns: list[ResourceSummary]
    derivation_function: ResourceSummary | None
    derivation_properties: list[ResourceSummary]
    group_by_columns: list[ResourceSummary]
    aggregated_columns: list[AggregatedColumnDescription]
    transform_conditions: list[TransformConditionDescription]
    transform_outputs: list[TransformOutputDescription]
    source_caveats: list[CaveatDescription]


@dataclass(frozen=True)
class ProfileRunCandidate:
    evidence_iri: str
    returned_profile_count: int
    profile_observation_iris: list[str]
    dataset_profile_row_counts: list[int]
    dataset_profile_row_count_bases: dict[str, list[str]]
    row_count_snapshot_matches: bool
    row_count_snapshot_basis: str | None
    shared_by_all_returned_profiles: bool


@dataclass(frozen=True)
class ProfileSummary:
    returned_dataset_profile_count: int
    returned_mapped_column_profile_count: int
    returned_unmapped_column_profile_count: int
    returned_profile_count: int
    total_dataset_profile_count: int
    total_mapped_column_profile_count: int
    total_unmapped_column_profile_count: int
    total_profile_count: int
    omitted_dataset_profile_count: int
    omitted_mapped_column_profile_count: int
    omitted_unmapped_column_profile_count: int
    omitted_profile_count: int
    mapped_profiled_column_count: int
    evidence_iris: list[str]
    evidence_profile_counts: dict[str, int]
    shared_evidence_iris: list[str]
    profile_run_candidates: list[ProfileRunCandidate]
    handoff_note: str


@dataclass(frozen=True)
class ProfileRunDescription:
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    row_count_snapshot: int | None
    dataset_profile_row_counts: list[int]
    dataset_profile_row_count_bases: dict[str, list[str]]
    row_count_snapshot_matches: bool
    row_count_snapshot_basis: str | None
    returned_dataset_profile_count: int
    returned_mapped_column_profile_count: int
    returned_unmapped_column_profile_count: int
    returned_profile_count: int
    total_dataset_profile_count: int
    total_mapped_column_profile_count: int
    total_unmapped_column_profile_count: int
    total_profile_count: int
    omitted_dataset_profile_count: int
    omitted_mapped_column_profile_count: int
    omitted_unmapped_column_profile_count: int
    omitted_profile_count: int
    profile_observation_iris: list[str]
    dataset_profile_observations: list[ProfileObservationSummary]
    mapped_column_profile_observations: list[ProfileObservationSummary]
    unmapped_column_profile_observations: list[ProfileObservationSummary]
    retrieval_note: str
    suggested_next_actions: list[SuggestedNextAction] = field(default_factory=list)
    suggested_next_calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileMapUpdateRecommendation:
    recommendation_index: int
    kind: str
    action: str
    resource: ResourceSummary
    predicate: str
    current_value: Any
    observed_value: Any
    observed_count: int | None
    sample_size: int | None
    sample_scope: str | None
    sample_method: str | None
    profile_row_count: int | None
    profile_observation_iri: str
    evidence_iri: str
    basis: str
    confidence: str
    helper_name: str
    helper_arguments: dict[str, Any]
    rationale: str
    default_stageable: bool = True
    default_skip_reason: str | None = None
    duplicate_group_key: str = ""
    duplicate_count: int = 1
    duplicate_recommendation_indexes: list[int] = field(default_factory=list)
    duplicate_profile_observation_iris: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileScalarConflictRecommendationContext:
    recommendation_index: int
    profile_observation_iri: str
    observed_count: int | None
    sample_size: int | None
    sample_scope: str | None
    sample_method: str | None
    profile_row_count: int | None
    basis: str
    confidence: str


@dataclass(frozen=True)
class ProfileScalarConflictOption:
    observed_value: Any
    representative_recommendation_index: int
    recommendation_indexes: list[int]
    duplicate_recommendation_indexes: list[int]
    duplicate_profile_observation_iris: list[str]
    recommendation_contexts: list[ProfileScalarConflictRecommendationContext]
    suggested_next_action: SuggestedNextAction
    suggested_next_call: str


@dataclass(frozen=True)
class ProfileScalarConflictGroup:
    conflict_group_index: int
    evidence_iri: str
    resource: ResourceSummary
    predicate: str
    kind: str
    current_value: Any
    option_count: int
    options: list[ProfileScalarConflictOption]
    review_note: str


@dataclass(frozen=True)
class ProfileMetricVocabularyAdvisory:
    profile_observation_iri: str
    observed_metric_iri: str
    metric_advisory_index: int
    evidence_iri: str
    metric: ResourceSummary
    target: ResourceSummary | None
    value: str
    value_datatype: str | None
    value_lang: str | None
    advisory_status: str
    definition_found: bool
    definition: ResourceSummary | None
    promotion_patterns: list[ResourceSummary]
    promotion_pattern_count: int
    mixed_support_patterns: list[ResourceSummary]
    mixed_support_pattern_count: int
    mixed_support_note: str | None
    context_patterns: list[ResourceSummary]
    context_pattern_count: int
    pending_staged_promotion_iris: list[str]
    pending_staged_promotion_count: int
    recommendation: str
    rationale: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    duplicate_group_key: str = ""
    duplicate_count: int = 1
    duplicate_advisory_indexes: list[int] = field(default_factory=list)
    duplicate_profile_observation_iris: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileTypeFindingAdvisory:
    profile_observation_iri: str
    type_advisory_index: int
    evidence_iri: str
    observed_column: ResourceSummary
    observed_column_name: str | None
    observed_physical_type: ResourceSummary | None
    observed_value_type: ResourceSummary | None
    map_column_found: bool
    current_physical_type: ResourceSummary | None
    current_value_type: ResourceSummary | None
    promotion_patterns: list[ResourceSummary]
    promotion_pattern_count: int
    mixed_support_patterns: list[ResourceSummary]
    mixed_support_pattern_count: int
    mixed_support_note: str | None
    advisory_status: str
    recommendation: str
    rationale: str
    routing_note: str
    related_recommendation_indexes: list[int]
    related_recommendation_kinds: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    pending_staged_promotion_iris: list[str] = field(default_factory=list)
    pending_staged_promotion_count: int = 0
    pending_staged_assertion_iris: list[str] = field(default_factory=list)
    pending_staged_assertion_count: int = 0
    duplicate_group_key: str = ""
    duplicate_count: int = 1
    duplicate_advisory_indexes: list[int] = field(default_factory=list)
    duplicate_profile_observation_iris: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileAdvisoryFollowthroughPlanItem:
    semantic_move: str
    review_lane: str
    route_group_key: str
    action_count: int
    tool_names: list[str]
    action_labels: list[str]
    suggested_next_calls: list[str]
    primary_tool_name: str | None
    primary_action_kind: str | None
    primary_action_writes_graph: bool
    primary_next_call: str | None
    metric_advisory_indexes: list[int]
    type_advisory_indexes: list[int]
    duplicate_group_keys: list[str]
    duplicate_advisory_indexes: list[int]
    duplicate_profile_observation_iris: list[str]
    advisory_status_counts: dict[str, int]
    route_step_keys: list[str]
    route_anchor_iris: list[str]
    route_pattern_iris: list[str]
    source_profile_advisories: list[dict[str, Any]]
    note: str


@dataclass(frozen=True)
class ProfileActionRouteSummary:
    action_group: str
    action_index: int
    tool_name: str
    mcp_tool_name: str
    action_label: str
    action_kind: str | None
    writes_graph: bool
    review_lane: str | None
    semantic_move: str | None
    route_group_key: str | None
    route_step_key: str | None
    source_kind: str | None
    advisory_indexes: list[int]
    recommendation_indexes: list[int]
    duplicate_group_keys: list[str]
    route_anchor_iris: list[str]
    route_pattern_iris: list[str]
    consumes_binding_keys: list[str]
    produces_binding_keys: list[str]
    requires_result_bindings: bool
    produces_result_bindings: bool
    unattended_choice_role: str | None
    unattended_recommended: bool
    argument_keys: list[str]
    has_arguments: bool
    has_call: bool


@dataclass(frozen=True)
class ProfileMixedSupportReviewGroup:
    group_index: int
    pattern_iris: list[str]
    pattern_count: int
    review_lanes: list[str]
    semantic_moves: list[str]
    route_group_keys: list[str]
    route_step_keys: list[str]
    route_anchor_iris: list[str]
    route_pattern_iris: list[str]
    action_count: int
    tool_names: list[str]
    action_labels: list[str]
    suggested_next_calls: list[str]
    metric_advisory_indexes: list[int]
    type_advisory_indexes: list[int]
    duplicate_group_keys: list[str]
    duplicate_advisory_indexes: list[int]
    duplicate_profile_observation_iris: list[str]
    source_profile_advisories: list[dict[str, Any]]
    note: str


@dataclass(frozen=True)
class ProfileFollowthroughBindingResolution:
    binding_key: str
    status: str
    value: Any | None
    source_tool_name: str | None
    source_result_field: str | None
    target_tool_name: str | None
    target_argument: str | None
    append: bool
    review_lane: str | None
    route_group_key: str | None
    action_group: str
    action_index: int
    action_label: str
    note: str


@dataclass(frozen=True)
class ProfileFollowthroughActionResolution:
    action_group: str
    action_index: int
    action_label: str
    tool_name: str
    semantic_move: str | None
    binding_status: str
    applied_binding_keys: list[str]
    missing_binding_keys: list[str]
    action: SuggestedNextAction


@dataclass(frozen=True)
class ProfileFollowthroughRevisionCheck:
    staged_revision_iri: str
    status_before: str
    decision_before: str
    routing_decision_before: str
    blocking_reasons_before: list[str]
    next_action_before: RevisionNextAction | None
    restage_performed: bool
    restaged_revision_iri: str | None
    status_after: str | None
    decision_after: str | None
    routing_decision_after: str | None
    next_action_after: RevisionNextAction | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    note: str


@dataclass(frozen=True)
class ProfileFollowthroughPlan:
    result_kind: str
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    graph: str | None
    draft: ProfileMapUpdateDraft
    result_binding_keys: list[str]
    binding_resolution_count: int
    binding_resolutions: list[ProfileFollowthroughBindingResolution]
    action_resolutions: list[ProfileFollowthroughActionResolution]
    action_resolution_groups: dict[str, list[ProfileFollowthroughActionResolution]]
    resolved_action_count: int
    missing_binding_keys: list[str]
    missing_binding_action_count: int
    produced_bindings: list[dict[str, Any]]
    produced_binding_count: int
    revision_checks: list[ProfileFollowthroughRevisionCheck]
    revision_check_count: int
    restage_stale_revisions: bool
    restaged_revision_iris: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    suggested_next_action_groups: dict[str, list[SuggestedNextAction]]
    suggested_next_call_groups: dict[str, list[str]]
    profile_type_assertion_batch_plan: dict[str, Any]
    suggested_next_action_summaries: list[ProfileActionRouteSummary]
    suggested_next_action_group_summaries: dict[
        str,
        list[ProfileActionRouteSummary],
    ]
    review_note: str


@dataclass(frozen=True)
class ProfileMapUpdateDraft:
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    map_dataset_found: bool
    status: str
    pending_staged_profile_update_iris: list[str]
    pending_staged_profile_update_count: int
    profile_observation_iris: list[str]
    recommendations: list[ProfileMapUpdateRecommendation]
    recommendation_count: int
    representative_recommendation_indexes: list[int]
    profile_quality_summary: dict[str, Any]
    sampled_evidence_caution: str | None
    scalar_conflict_groups: list[ProfileScalarConflictGroup]
    scalar_conflict_group_count: int
    metric_advisories: list[ProfileMetricVocabularyAdvisory]
    metric_advisory_count: int
    representative_metric_advisory_indexes: list[int]
    metric_advisory_status_counts: dict[str, int]
    type_advisories: list[ProfileTypeFindingAdvisory]
    type_advisory_count: int
    representative_type_advisory_indexes: list[int]
    type_advisory_status_counts: dict[str, int]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    suggested_next_action_groups: dict[str, list[SuggestedNextAction]]
    suggested_next_call_groups: dict[str, list[str]]
    suggested_next_action_summaries: list[ProfileActionRouteSummary]
    suggested_next_action_group_summaries: dict[
        str,
        list[ProfileActionRouteSummary],
    ]
    advisory_followthrough_plan: list[ProfileAdvisoryFollowthroughPlanItem]
    mixed_support_review_groups: list[ProfileMixedSupportReviewGroup]
    mixed_support_review_group_count: int
    review_note: str


@dataclass(frozen=True)
class ProfileMapUpdateStagingItem:
    recommendation_index: int
    kind: str
    action: str
    resource: ResourceSummary
    status: str
    reason: str | None
    basis: str
    confidence: str
    sample_size: int | None
    sample_scope: str | None
    sample_method: str | None
    profile_observation_iri: str
    supporting_profile_observation_iris: list[str]


@dataclass(frozen=True)
class ProfileMapUpdateStagingRecord:
    result_kind: str
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    map_dataset_found: bool
    recommendation_count: int
    accepted_recommendation_indexes: list[int]
    staged_recommendation_indexes: list[int]
    skipped_recommendation_indexes: list[int]
    not_selected_recommendation_indexes: list[int]
    status_counts: dict[str, int]
    items: list[ProfileMapUpdateStagingItem]
    metric_advisories: list[ProfileMetricVocabularyAdvisory]
    metric_advisory_count: int
    metric_advisory_status_counts: dict[str, int]
    metric_vocabulary_review_required: bool
    metric_advisory_suggested_next_actions: list[SuggestedNextAction]
    metric_advisory_suggested_next_calls: list[str]
    type_advisories: list[ProfileTypeFindingAdvisory]
    type_advisory_count: int
    type_advisory_status_counts: dict[str, int]
    type_review_required: bool
    type_advisory_suggested_next_actions: list[SuggestedNextAction]
    type_advisory_suggested_next_calls: list[str]
    revision_iri: str | None
    staged_revision: StagedGraphRevisionRecord | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    review_note: str


@dataclass(frozen=True)
class DatasetDescription:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    row_semantics: ResourceSummary | None
    entity_key: ResourceSummary | None
    snapshot_timestamp: ResourceSummary | None
    schema_stability: ResourceSummary | None
    row_count_snapshot: int | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None
    profile_summary: ProfileSummary
    profile_observations: list[ProfileObservationSummary]
    unmapped_column_profile_observations: list[ProfileObservationSummary]
    columns: list[ColumnDescription]
    path_templates: list[str]
    physical_layouts: list[PhysicalLayoutDescription]
    storage_accesses: list[StorageAccessDescription]
    partition_schemes: list[PartitionDescription]
    caveats: list[CaveatDescription]
    upstream_caveats: list[CaveatDescription]
    operational_warnings: list[QueryPlanningIssue]
    provenance: list[ResourceSummary]
    transformations: list[TransformationDescription]
    related_datasets: list[RelatedDatasetDescription]
    related_dataset_groups: list[RelatedDatasetGroup]
    relationships: list[RelationshipDescription]
    tuple_grains: list[TupleGrainDescription]
    linked_patterns: list[ResourceSummary]
    linked_pattern_reasons: list[LinkedPatternReason]


@dataclass(frozen=True)
class ObservationRecord:
    observation_iri: str
    observation_type: str
    evidence_iri: str | None
    observation_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class QueryResultRecord:
    observation_iri: str
    observation_type: str
    evidence_iri: str
    source_span_iri: str | None
    scanned_source_span_iris: list[str]
    execution_status: str
    engine: str | None
    query_source_path: str | None
    query_hash: str | None
    failure_summary: str | None
    result_sources: list[str]
    scanned_source_paths: list[str]
    scanned_source_handles: list[str]
    observation_triples: int
    evidence_triples: int
    source_span_triples: int
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class QueryEvidenceStorageOverlayDraft:
    result_kind: str
    helper: str
    mode: str
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    source_query_context_readiness: str
    source_query_context_issue_codes: list[str]
    source_profile_evidence: dict[str, Any]
    source_query_evidence: dict[str, Any]
    evidence_storage_route_candidates: list[dict[str, Any]]
    evidence_storage_route_candidate_count: int
    evidence_storage_route_candidate_total_count: int
    evidence_storage_route_candidates_truncated: bool
    profile_observation_iris: list[str]
    storage_access_iri: str
    physical_layout_iri: str
    reviewed_overlay: dict[str, Any]
    additions: list[dict[str, str]]
    changed_graphs: list[str]
    patches: list[StagedGraphPatchDescription]
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]
    validation_report_text: str
    review_note: str
    review_recommendation: str
    stage_arguments: dict[str, Any]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class QueryEvidenceStorageOverlayBlocker:
    result_kind: str
    helper: str
    mode: str
    dataset: ResourceSummary
    evidence: EvidenceDescription
    evidence_iri: str
    source_query_context_readiness: str
    source_query_context_issue_codes: list[str]
    source_profile_evidence: dict[str, Any]
    source_query_evidence: dict[str, Any]
    evidence_storage_route_candidates: list[dict[str, Any]]
    evidence_storage_route_candidate_count: int
    evidence_storage_route_candidate_total_count: int
    evidence_storage_route_candidates_truncated: bool
    missing_seed_terms: list[str]
    mutation_allowed_after: str
    note: str
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ClaimObservationRecord:
    observation_iri: str
    claim_iri: str
    evidence_iri: str
    source_span_iri: str | None
    observation_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class PatternRecord:
    pattern_iri: str
    evidence_iri: str | None
    source_span_iri: str | None
    pattern_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class DatasetProfileRecord:
    dataset_iri: str
    observation: ObservationRecord
    map_dataset: MapResourceRecord | None
    pattern: PatternRecord | None


@dataclass(frozen=True)
class ColumnProfileRecord:
    column_iri: str
    table_iri: str | None
    observation: ObservationRecord
    map_column: MapResourceRecord | None
    pattern: PatternRecord | None


@dataclass(frozen=True)
class ProfileBundleHandoffEntryPoints:
    dataset_iri: str
    shared_evidence_iri: str | None
    dataset_profile_observation_iri: str
    column_profile_observation_iris: list[str]
    profile_observation_iris: list[str]
    map_dataset_recorded: bool
    map_column_iris: list[str]
    updated_map_column_iris: list[str]
    mapped_profiled_column_iris: list[str]
    dataset_describe_available: bool
    profile_run_available: bool
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    handoff_note: str


@dataclass(frozen=True)
class ProfileBundleRecord:
    dataset_iri: str
    shared_evidence_iri: str | None
    dataset_profile: DatasetProfileRecord
    column_profiles: list[ColumnProfileRecord]
    handoff_entrypoints: ProfileBundleHandoffEntryPoints


@dataclass(frozen=True)
class DomainNetworkProfileRecord:
    dataset_iri: str
    evidence_iri: str | None
    analysis_view: MapResourceRecord | None
    caveat: MapResourceRecord | None
    coverage_profile: DatasetProfileRecord
    domain_pair_profile: DatasetProfileRecord | None
    sender_domain_profile: DatasetProfileRecord | None
    recipient_domain_profile: DatasetProfileRecord | None
    pattern: PatternRecord | None
    profile_observation_iris: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ClaimReconsiderationRecord:
    reconsideration_iri: str
    newer_claim_iri: str
    older_claim_iri: str
    relation: str
    relation_label: str | None
    direct_predicate: str
    older_claim_status: str | None
    evidence_iri: str | None
    source_span_iri: str | None
    reconsideration_triples: int
    evidence_triples: int
    status_triples: int


@dataclass(frozen=True)
class SourceSpanDescription:
    iri: str
    source_path: str | None
    source_section: str | None
    start_line: int | None
    end_line: int | None
    source_kind: str | None
    source_kind_label: str | None


@dataclass(frozen=True)
class EvidenceDescription:
    iri: str
    label: str | None
    summary: str | None
    sources: list[str]
    source_spans: list[SourceSpanDescription]
    scanned_source_handles: list[str]
    query_execution_status: str | None
    query_engine: str | None
    query_hash: str | None


@dataclass(frozen=True)
class ClaimReconsiderationDescription:
    iri: str
    label: str | None
    summary: str | None
    rationale: str | None
    relation: str | None
    relation_label: str | None
    newer_claim: ResourceSummary | None
    older_claim: ResourceSummary | None
    evidence: list[EvidenceDescription]
    reconsidered_at: str | None
    reconsidered_by: str | None


@dataclass(frozen=True)
class ClaimDescription:
    iri: str
    label: str | None
    claim_text: str | None
    claim_kind: str | None
    claim_kind_label: str | None
    claim_targets: list[ResourceSummary]
    confidence: str | None
    confidence_label: str | None
    observation_status: str | None
    observation_status_label: str | None
    proposed_assertions: list[ResourceSummary]
    lifecycle_summary: str | None
    outgoing_reconsiderations: list[ClaimReconsiderationDescription]
    incoming_reconsiderations: list[ClaimReconsiderationDescription]


@dataclass(frozen=True)
class PatternDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    pattern_text: str | None
    rationale: str | None
    pattern_targets: list[ResourceSummary]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ClaimDescription]
    evidence: list[EvidenceDescription]
    confidence: str | None
    confidence_label: str | None
    observation_status: str | None
    observation_status_label: str | None
    pattern_stability: str | None
    pattern_stability_label: str | None
    map_implications: list[ResourceSummary]


@dataclass(frozen=True)
class MapResourceRecord:
    iri: str
    resource_type: str
    graph: str
    triples: int


@dataclass(frozen=True)
class MapTableBundleRecord:
    dataset: MapResourceRecord
    storage_access: MapResourceRecord | None
    physical_layout: MapResourceRecord | None
    columns: list[MapResourceRecord]
    column_iris: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ProfiledParquetTableRecord:
    dataset_iri: str
    shared_evidence_iri: str
    table_bundle: MapTableBundleRecord
    profile_bundle: ProfileBundleRecord
    profile_observation_count: int
    profile_draft_recommendation_count: int
    query_readiness: str
    query_issue_codes: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ProfileToCapsuleManifestRecord:
    manifest_format: str
    caveat_records: list[MapResourceRecord]
    table_records: list[ProfiledParquetTableRecord]
    analysis_view_bundle: AnalysisViewBundleRecord | None
    domain_network_profile_records: list[DomainNetworkProfileRecord]
    caveat_iris: list[str]
    table_iris: list[str]
    shared_evidence_iris: list[str]
    analysis_view_iris: list[str]
    domain_network_profile_evidence_iris: list[str]
    domain_network_pattern_iris: list[str]
    caveat_count: int
    table_count: int
    analysis_view_count: int
    domain_network_profile_count: int
    domain_network_profile_observation_count: int
    profile_observation_count: int
    query_readiness_counts: dict[str, int]
    query_issue_code_counts: dict[str, int]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ResourceTriple:
    graph: str
    subject: str
    subject_kind: str
    subject_label: str | None
    subject_types: list[str]
    predicate: str
    predicate_label: str | None
    object: str
    object_kind: str
    object_label: str | None
    object_types: list[str]
    object_datatype: str | None
    object_lang: str | None


@dataclass(frozen=True)
class ResourceContext:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    claim: ClaimDescription | None
    outgoing: list[ResourceTriple]
    incoming: list[ResourceTriple]
    blank_node_triples: list[ResourceTriple]
    limit: int
    outgoing_offset: int
    incoming_offset: int
    outgoing_total_count: int
    outgoing_returned_count: int
    outgoing_omitted_count: int
    incoming_total_count: int
    incoming_returned_count: int
    incoming_omitted_count: int
    include_blank_node_closure: bool
    blank_node_depth: int
    blank_node_limit: int
    blank_node_total_count: int
    blank_node_returned_count: int
    blank_node_omitted_count: int
    blank_node_depth_exhausted: bool
    blank_node_unvisited_count: int


@dataclass(frozen=True)
class AssertionValue:
    value: str
    value_label: str | None
    value_kind: str
    datatype: str | None = None
    lang: str | None = None
    resource: ResourceSummary | None = None
    caveat: CaveatDescription | None = None


@dataclass(frozen=True)
class AssertionSupportRoute:
    resource: ResourceSummary
    resource_kind: str
    route_type: str
    route_label: str
    matched_resource: ResourceSummary | None


@dataclass(frozen=True)
class AssertionSupportRouteSummary:
    rank: int
    resource: ResourceSummary
    resource_kind: str
    route_count: int
    route_types: list[str]
    route_labels: list[str]
    matched_resources: list[ResourceSummary]
    strongest_route_type: str
    strongest_route_label: str
    relevance_tier: str
    generic_value_only: bool
    route_note: str


@dataclass(frozen=True)
class AssertionPredicateHint:
    predicate: str
    predicate_curie: str | None
    predicate_label: str | None
    predicate_description: str | None
    triple_count: int
    sample_values: list[AssertionValue]


@dataclass(frozen=True)
class SuggestedNextAction:
    action_label: str
    tool_name: str
    mcp_tool_name: str
    arguments: dict[str, Any]
    reason: str
    call: str


@dataclass(frozen=True)
class TemplatedSuggestedNextAction(SuggestedNextAction):
    required_extra_arguments: list[str]
    placeholder_fields: list[str]
    reviewed_value_fields: list[str]


@dataclass(frozen=True)
class EffectAnnotatedSuggestedNextAction(SuggestedNextAction):
    mutation_scope: str
    mutates_project_graph: bool
    writes_history: bool
    writes_files: bool
    writes_storage: bool = False


@dataclass(frozen=True)
class ProfileAdvisorySuggestedNextAction(SuggestedNextAction):
    source_profile_advisory: dict[str, Any]
    review_lane: str | None = None
    route_group_key: str | None = None
    route_step_key: str | None = None
    semantic_move: str | None = None
    unattended_choice_role: str | None = None
    unattended_recommended: bool = False


@dataclass(frozen=True)
class ProfileMapUpdateSuggestedNextAction(SuggestedNextAction):
    source_profile_map_update: dict[str, Any]


@dataclass(frozen=True)
class ProfileScalarConflictSuggestedNextAction(SuggestedNextAction):
    source_scalar_conflict: dict[str, Any]


@dataclass(frozen=True)
class ProfileEvidenceSuggestedNextAction(SuggestedNextAction):
    source_profile_evidence: dict[str, Any]


@dataclass(frozen=True)
class QueryEvidenceOverlaySuggestedNextAction(SuggestedNextAction):
    source_profile_evidence: dict[str, Any]
    source_query_evidence: dict[str, Any]
    evidence_storage_route_candidates: list[dict[str, Any]]
    evidence_storage_route_candidate_count: int
    evidence_storage_route_candidate_total_count: int
    evidence_storage_route_candidates_truncated: bool
    required_extra_arguments: list[str]
    placeholder_fields: list[str]
    reviewed_value_fields: list[str]
    template_note: str


@dataclass(frozen=True)
class QueryPlanSuggestedNextAction(SuggestedNextAction):
    route_card: dict[str, Any]
    unattended_recommended: bool = True
    unattended_caution: str | None = None
    unattended_review_reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfileQueryContextSuggestedNextAction(SuggestedNextAction):
    source_query_context: dict[str, Any]


@dataclass(frozen=True)
class ProfileMapUpdateRerunSuggestedNextAction(SuggestedNextAction):
    preconditions: dict[str, Any]


@dataclass(frozen=True)
class RevisionNextAction:
    action_type: str
    queue: str
    action_label: str
    tool_name: str | None
    mcp_tool_name: str | None
    arguments: dict[str, Any]
    reason: str
    call: str | None
    source: str
    mutation_scope: str = field(init=False)
    mutates_project_graph: bool = field(init=False)
    writes_history: bool = field(init=False)
    writes_files: bool = field(init=False)
    writes_storage: bool = field(init=False)

    def __post_init__(self) -> None:
        effect = staged_action_effect_metadata(self.tool_name, self.arguments)
        for key, value in effect.items():
            object.__setattr__(self, key, value)


@dataclass(frozen=True)
class RevisionNextActionQueueItem:
    row_iri: str
    queue: str
    action_type: str
    action_label: str
    tool_name: str | None
    mcp_tool_name: str | None
    resolved_target_iri: str | None
    resolved_target_iri_source: str | None
    resolved_target_record_kind: str | None
    row_is_target: bool
    call: str | None
    source: str
    record_kind: str | None
    application_status: str | None
    application_decision: str | None
    stale_resolution_state: str | None
    staged_validation_status: str | None
    semantic_risk_level: str | None
    semantic_risk_reasons: list[str]
    profile_route_keys: list[str]
    profile_gate_label: str | None
    profile_generic_queue_caution: str | None
    profile_semantic_apply_role: str | None
    profile_apply_cardinality: str | None
    profile_safe_single_apply_candidate: bool | None
    profile_bulk_apply_allowed: bool | None
    profile_semantic_apply_gate_reason: str | None
    alternative_gate_status: str | None
    alternative_semantic_review_required: bool
    requires_semantic_review_before_mutation: bool | None
    alternative_applied_source_iri: str | None
    alternative_applied_revision_iri: str | None
    alternative_set_iris: list[str]
    alternative_set_source_iri: str | None
    alternative_set_role: str | None


@dataclass(frozen=True)
class AssertionSupportDescription:
    graph: str | None
    subject: ResourceSummary
    owner_dataset: ResourceSummary | None
    predicate: str
    predicate_label: str | None
    requested_object: AssertionValue | None
    assertion_present: bool
    matching_triples: list[ResourceTriple]
    same_subject_predicate_triples: list[ResourceTriple]
    target_resources: list[ResourceSummary]
    nearby_caveats: list[CaveatDescription]
    nearby_caveat_links: list[AssertionSupportCaveatLink]
    nearby_context_triples: list[ResourceTriple]
    related_observations: list[ResourceSummary]
    related_claims: list[ResourceSummary]
    related_patterns: list[ResourceSummary]
    related_evidence: list[ResourceSummary]
    related_revisions: list[ResourceSummary]
    related_routes: list[AssertionSupportRoute]
    related_route_summaries: list[AssertionSupportRouteSummary]
    predicate_hints: list[AssertionPredicateHint]
    context_note: str
    support_scope_note: str
    absence_note: str | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class MapAssertionJudgementValue:
    value: str
    label: str | None
    value_kind: str
    datatype: str | None = None
    lang: str | None = None
    caveat: CaveatDescription | None = None


@dataclass(frozen=True)
class MapAssertionJudgementCaveat:
    caveat_iri: str
    caveat_label: str | None
    scope: str
    route_label: str
    via_resource: ResourceSummary
    matched_resource: ResourceSummary
    description: str | None
    impact: str | None
    severity_label: str | None


@dataclass(frozen=True)
class MapAssertionJudgementRoute:
    rank: int
    resource_iri: str
    resource_label: str | None
    resource_kind: str
    strongest_route_label: str
    route_count: int
    route_note: str
    matched_resources: list[ResourceSummary]
    generic_value_only: bool
    relevance_note: str | None


@dataclass(frozen=True)
class MapAssertionJudgementImpact:
    impact_type: str
    severity: str
    message: str
    removed_values: list[MapAssertionJudgementValue]
    added_values: list[MapAssertionJudgementValue]


@dataclass(frozen=True)
class MapAssertionJudgementValueTypeContext:
    value_type: ResourceSummary
    required_physical_type: MapAssertionJudgementValue | None
    current_physical_type_matches: bool | None
    proposed_physical_type_matches: bool | None
    note: str


@dataclass(frozen=True)
class MapAssertionJudgementPanel:
    headline: str
    recommendation: str | None
    assertion_present_before: bool
    current_values: list[MapAssertionJudgementValue]
    proposed_value: MapAssertionJudgementValue | None
    target_value: MapAssertionJudgementValue | None
    removed_value: MapAssertionJudgementValue | None
    absence_note: str | None
    semantic_risk_level: str
    semantic_risk_reasons: list[str]
    value_type_context: list[MapAssertionJudgementValueTypeContext]
    why_current_value_may_be_intentional: list[str]
    caveats: list[MapAssertionJudgementCaveat]
    strongest_routes: list[MapAssertionJudgementRoute]
    impacts: list[MapAssertionJudgementImpact]
    safety_notes: list[str]


@dataclass(frozen=True)
class StagedMapAssertionChangeRecord:
    revision_iri: str
    change_kind: str
    graph: str
    subject: str
    predicate: str
    object_value: str | None
    object_kind: str
    object_datatype: str | None
    object_lang: str | None
    assertion_present_before: bool
    current_values_before: list[ResourceTriple]
    additions: list[dict[str, str]]
    removals: list[dict[str, str]]
    assertion_support: AssertionSupportDescription
    staged_revision: StagedGraphRevisionRecord
    judgement_panel: MapAssertionJudgementPanel
    review_note: str
    review_recommendation: str | None
    profile_route_source_count: int


@dataclass(frozen=True)
class DraftMapAssertionChangeRecord:
    result_kind: str
    change_kind: str
    graph: str
    subject: str
    predicate: str
    object_value: str | None
    object_kind: str
    object_datatype: str | None
    object_lang: str | None
    assertion_present_before: bool
    current_values_before: list[ResourceTriple]
    additions: list[dict[str, str]]
    removals: list[dict[str, str]]
    changed_graphs: list[str]
    patches: list[StagedGraphPatchDescription]
    impacts: list[StagedRevisionImpact]
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]
    validation_report_text: str
    assertion_support: AssertionSupportDescription
    judgement_panel: MapAssertionJudgementPanel
    review_note: str
    review_recommendation: str | None
    stage_arguments: dict[str, Any]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class _MapAssertionChangePrepared:
    change_kind: str
    graph: str
    subject: str
    predicate: str
    object_value: str | None
    object_kind: str
    object_datatype: str | None
    object_lang: str | None
    rationale: str
    additions: list[dict[str, str]]
    removals: list[dict[str, str]]
    summary: str
    review_note: str
    review_recommendation: str | None
    assertion_support: AssertionSupportDescription
    assertion_present_before: bool
    current_values_before: list[ResourceTriple]
    supporting_observations: list[str]
    supporting_claims: list[str]
    supporting_patterns: list[str]
    revision_anchors: list[str]
    evidence: list[str]
    stage_arguments: dict[str, Any]


@dataclass(frozen=True)
class ContextSliceRoute:
    route: str
    route_label: str
    source_iri: str | None
    source_label: str | None
    depth: int


@dataclass(frozen=True)
class ContextSliceRouteLegend:
    route: str
    route_label: str
    meaning: str
    priority: int
    count: int


@dataclass(frozen=True)
class ContextSliceResource:
    iri: str
    label: str | None
    description: str | None
    types: list[str]
    graphs: list[str]
    surface_role: str
    referenced_only: bool
    primary_route: ContextSliceRoute
    routes: list[ContextSliceRoute]


@dataclass(frozen=True)
class ContextSlice:
    profile: str
    seeds: list[ResourceSummary]
    reading_order: list[str]
    resources: list[ContextSliceResource]
    resource_count: int
    route_legend: list[ContextSliceRouteLegend]
    route_counts: dict[str, int]
    graph_counts: dict[str, int]
    triples: list[ResourceTriple] = field(metadata={"doxabase_internal": True})
    triple_count: int
    returned_triple_count: int
    candidate_triple_count: int
    omitted_triple_count: int
    max_triples: int
    truncated: bool
    truncation_scope: str
    trig: str | None
    sensitive_literal_count: int
    returned_match_count: int
    omitted_match_count: int
    privacy_scan_limit: int
    matches: list[SensitiveLiteralMatch]
    privacy_warnings: list[str]
    scanner_note: str | None
    seed_profile_observations: list[ProfileObservationSummary]
    dataset_contexts: list[DatasetDescription] = field(metadata={"doxabase_internal": True})
    pattern_contexts: list[PatternDescription] = field(metadata={"doxabase_internal": True})
    warnings: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]
    shareability_hints: list[str] = field(default_factory=list)
    shareability_hint_count: int = 0
    returned_shareability_hint_count: int = 0
    omitted_shareability_hint_count: int = 0
    shareability_hint_matches: list[ShareabilityHintMatch] = field(
        default_factory=list
    )
    artifact_disposition: str = DEFAULT_ARTIFACT_DISPOSITION
    git_safe: bool = False


@dataclass(frozen=True)
class SearchMatch:
    iri: str
    graph: str
    label: str | None
    types: list[str]
    predicate: str
    predicate_label: str | None
    text: str
    snippet: str


@dataclass(frozen=True)
class SearchScopeHint:
    status: str
    message: str
    seed_match_count: int
    project_match_count: int
    seed_graphs: list[str]
    suggested_graphs: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class SearchResults:
    query: str
    graph: str | None
    matches: list[SearchMatch]
    limit: int
    offset: int
    returned_count: int
    total_count: int
    omitted_count: int
    has_more: bool
    next_offset: int | None
    scope_hint: SearchScopeHint | None = None
    suggested_next_actions: list[SuggestedNextAction] = field(default_factory=list)
    suggested_next_calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StagedPatchPayloadSearchMatch:
    revision_iri: str
    revision_summary: str | None
    revision_application_status: str | None
    revision_is_current_staged_work: bool | None
    patch_iri: str
    graph: str
    target_graph: str | None
    operation: str | None
    operation_label: str | None
    patch_role: str | None
    patch_role_label: str | None
    sequence_index: int | None
    triple_count: int | None
    text: str
    snippet: str
    matched_term_roles: list[str]
    patch_subject_iris: list[str]
    parsed_resource_iris: list[str]
    parsed_resource_count: int
    parse_error: str | None
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class StagedPatchPayloadSearchResults:
    query: str
    graph: str | None
    current_staged_work_only: bool
    matches: list[StagedPatchPayloadSearchMatch]
    count: int
    returned_count: int
    total_count: int
    limit: int
    offset: int
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_calls: list[str]


@dataclass(frozen=True)
class ValidationResult:
    conforms: bool
    report_text: str
    result_count: int
    scope: str
    results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class _StagedGraphPatchPreview:
    changed_graphs: list[str]
    patch_records: list[StagedGraphPatchRecord]
    patch_descriptions: list[StagedGraphPatchDescription]
    validation: ValidationResult


def _search_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", query)
    if not tokens:
        raise DoxaBaseError("Search query must contain at least one searchable token")
    return [token.lower() for token in tokens]



__all__ = [
    "DoxaBaseError",
    "ImmutableGraphError",
    "NamedGraphInfo",
    "GraphOverview",
    "ProjectBriefDatasetQuerySummary",
    "ProjectBriefProfileDraftSummary",
    "ProjectBriefDatasetProfileSummary",
    "ProjectBriefDatasetSummary",
    "ProjectBriefStagedReviewItem",
    "ProjectBriefStagedReviewSummary",
    "ProjectBriefRecommendedTask",
    "ProjectBriefHealthTask",
    "ProjectBriefFrontierStatus",
    "ProjectBrief",
    "SensitiveLiteralMatch",
    "SensitiveLiteralScan",
    "ExportPreflightMatch",
    "ShareabilityHintMatch",
    "ExportPreflightRecord",
    "GraphExportRecord",
    "ContextSliceExportRecord",
    "GraphTripleReplacementRecord",
    "GraphRevisionRecord",
    "StagedRevisionReviewResolutionSummary",
    "StagedRevisionReviewDecisionRecord",
    "RevisionSnapshotBundleExportRecord",
    "HandoffBundleExportRecord",
    "RevisionSnapshotBundleImportRecord",
    "HandoffBundleRecoverySummary",
    "HandoffBundleImportRecord",
    "StagedGraphPatchRecord",
    "ValidationDiagnostic",
    "StagedGraphRevisionRecord",
    "RestagedGraphRevisionRecord",
    "StagedPatchApplyCheck",
    "StagedPatchRepairPlan",
    "StagedRevisionEffectiveDeltaSummary",
    "StagedRevisionAlternativeGate",
    "StagedGraphCountDrift",
    "GraphTripleDescription",
    "ChangedGraphResourceSummary",
    "StagedGraphSnapshotDrift",
    "StagedRevisionExactDriftSummary",
    "AppliedRevisionGraphSnapshotDiff",
    "AppliedRevisionDiffDescription",
    "StagedRevisionApplyCheck",
    "StagedRevisionApplySummary",
    "StagedRevisionRebaseLineageContext",
    "StagedRevisionRebaseCandidate",
    "StagedRevisionRebaseDraft",
    "SystematisationFramingRecord",
    "SystematisationSharedPatchSummary",
    "SystematisationWarningRecord",
    "SharedSemanticContextBundleWarning",
    "SystematisationDraftRecord",
    "SystematisationSharedContextRerunFraming",
    "SystematisationSharedContextRerunDraft",
    "PostApplyRecheckRevision",
    "AppliedStagedRevisionRecord",
    "StagedGraphRevisionExportRecord",
    "StagedGraphRevisionExportSummary",
    "StagedGraphRevisionSnapshotEvidenceRow",
    "StagedGraphRevisionSnapshotEvidenceSummary",
    "StagedGraphRevisionReviewSequenceItem",
    "StagedGraphRevisionChooseOneGroup",
    "StagedGraphRevisionModellingChoiceRow",
    "StagedGraphRevisionBundleSummary",
    "StagedGraphRevisionsExportRecord",
    "ProfileInsightReviewCandidate",
    "ProfileInsightOpenReviewAction",
    "ProfileInsightOpenReviewLane",
    "ProfileInsightReviewBundleRecord",
    "StagedGraphRevisionBatchRestageItem",
    "StagedGraphRevisionBatchRestageRecord",
    "StagedRevisionRecoveryLane",
    "StagedRevisionResolvedTargetGroup",
    "StagedRevisionMutationFrontierItem",
    "StagedRevisionRecoveryUnattendedStep",
    "StagedRevisionRecoveryPlan",
    "StagedRevisionRecoverySessionSourceState",
    "StagedRevisionRecoverySessionDescription",
    "_StagedRevisionApplicationPreview",
    "_StagedRevisionDriftTerms",
    "_ChangedGraphResourceAccumulator",
    "GraphSnapshotDescription",
    "RevisionSnapshotEvidenceStatus",
    "RevisionGraphSnapshotDescription",
    "StagedGraphPatchDescription",
    "StagedRevisionImpactValue",
    "StagedRevisionImpact",
    "StagedRevisionStoredReviewNoteSignals",
    "StagedRevisionStoredReviewSupportCounts",
    "StagedRevisionStoredReviewContext",
    "AppliedStagedRevisionSourcePatchSummary",
    "AppliedStagedRevisionSourceSummary",
    "GraphRevisionDescription",
    "GraphRevisionListItem",
    "GraphRevisionList",
    "GraphVersionListItem",
    "GraphVersionList",
    "GraphVersionRevisionContext",
    "GraphVersionDiffDescription",
    "RevisionLineageDescription",
    "ResourceRevisionPatchMention",
    "_ResourceRevisionPatchMentionScan",
    "ResourceRevisionPatchMentionScanSummary",
    "ResourceRevisionListItem",
    "ResourceRevisionTimelineEvent",
    "ResourceRevisionList",
    "ResourceAppliedRevisionGraphDiffSummary",
    "ResourceAppliedRevisionDiffSummary",
    "ResourceRevisionLineageDescription",
    "StagedGraphRevisionDescription",
    "EntityRow",
    "EntityList",
    "ResourceSummary",
    "ObservedValueFrequencySummary",
    "ObservedProfileMetricSummary",
    "ProfileObservationSummary",
    "ColumnDescription",
    "PhysicalLayoutDescription",
    "StorageAccessDescription",
    "PartitionDescription",
    "QueryPlanningIssue",
    "QueryRepairActionGroup",
    "QueryTargetCandidate",
    "QueryTargetDecision",
    "QueryPlanningContext",
    "DraftQueryPlanEngine",
    "DraftQueryPlanSourceContext",
    "DraftQueryPlanScan",
    "DraftQueryPlanBindingColumnMatch",
    "DraftQueryPlanBinding",
    "DraftQueryPlanStorageEnvironment",
    "DraftQueryPlanReviewGate",
    "DraftQueryPlanHandoffSummary",
    "DraftQueryPlan",
    "RelatedDatasetDescription",
    "RelatedDatasetReasonTag",
    "RelatedDatasetReason",
    "RelatedDatasetGroup",
    "LinkedPatternMatch",
    "LinkedPatternMatchGroup",
    "LinkedPatternReason",
    "CaveatDescription",
    "AssertionSupportCaveatLink",
    "TransformationDescription",
    "AnalysisDenominatorDescription",
    "QuerySnippetDescription",
    "AnalysisViewDescription",
    "AnalysisViewBundleRecord",
    "AnalysisArtifactRecord",
    "AnalysisQueryRecipeRecord",
    "AnalysisFollowupTaskRecord",
    "AnalysisPacketRecord",
    "AggregatedColumnDescription",
    "RelationshipEndpointDescription",
    "TransformConditionDescription",
    "GrainComponentDescription",
    "TupleGrainDescription",
    "TransformOutputDescription",
    "RelationshipDescription",
    "ProfileRunCandidate",
    "ProfileSummary",
    "ProfileRunDescription",
    "ProfileMapUpdateRecommendation",
    "ProfileScalarConflictRecommendationContext",
    "ProfileScalarConflictOption",
    "ProfileScalarConflictGroup",
    "ProfileMetricVocabularyAdvisory",
    "ProfileTypeFindingAdvisory",
    "ProfileAdvisoryFollowthroughPlanItem",
    "ProfileActionRouteSummary",
    "ProfileMixedSupportReviewGroup",
    "ProfileFollowthroughBindingResolution",
    "ProfileFollowthroughActionResolution",
    "ProfileFollowthroughRevisionCheck",
    "ProfileFollowthroughPlan",
    "ProfileMapUpdateDraft",
    "ProfileMapUpdateStagingItem",
    "ProfileMapUpdateStagingRecord",
    "DatasetDescription",
    "ObservationRecord",
    "QueryResultRecord",
    "QueryEvidenceStorageOverlayDraft",
    "QueryEvidenceStorageOverlayBlocker",
    "ClaimObservationRecord",
    "PatternRecord",
    "DatasetProfileRecord",
    "ColumnProfileRecord",
    "ProfileBundleHandoffEntryPoints",
    "ProfileBundleRecord",
    "DomainNetworkProfileRecord",
    "ClaimReconsiderationRecord",
    "SourceSpanDescription",
    "EvidenceDescription",
    "ClaimReconsiderationDescription",
    "ClaimDescription",
    "PatternDescription",
    "MapResourceRecord",
    "MapTableBundleRecord",
    "ProfiledParquetTableRecord",
    "ProfileToCapsuleManifestRecord",
    "ResourceTriple",
    "ResourceContext",
    "AssertionValue",
    "AssertionSupportRoute",
    "AssertionSupportRouteSummary",
    "AssertionPredicateHint",
    "SuggestedNextAction",
    "TemplatedSuggestedNextAction",
    "EffectAnnotatedSuggestedNextAction",
    "ProfileAdvisorySuggestedNextAction",
    "ProfileMapUpdateSuggestedNextAction",
    "ProfileScalarConflictSuggestedNextAction",
    "ProfileEvidenceSuggestedNextAction",
    "QueryEvidenceOverlaySuggestedNextAction",
    "QueryPlanSuggestedNextAction",
    "ProfileQueryContextSuggestedNextAction",
    "ProfileMapUpdateRerunSuggestedNextAction",
    "RevisionNextAction",
    "RevisionNextActionQueueItem",
    "AssertionSupportDescription",
    "MapAssertionJudgementValue",
    "MapAssertionJudgementCaveat",
    "MapAssertionJudgementRoute",
    "MapAssertionJudgementImpact",
    "MapAssertionJudgementValueTypeContext",
    "MapAssertionJudgementPanel",
    "StagedMapAssertionChangeRecord",
    "DraftMapAssertionChangeRecord",
    "_MapAssertionChangePrepared",
    "ContextSliceRoute",
    "ContextSliceRouteLegend",
    "ContextSliceResource",
    "ContextSlice",
    "SearchMatch",
    "SearchScopeHint",
    "SearchResults",
    "StagedPatchPayloadSearchMatch",
    "StagedPatchPayloadSearchResults",
    "ValidationResult",
    "_StagedGraphPatchPreview",
    "_search_tokens",
]
