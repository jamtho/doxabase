"""Capsule, brief, export, staged revision, and recovery record types.

Mechanically split from doxabase.core._types; classes are verbatim and
order-preserved. Part 1 of 2; ``doxabase.core._types`` re-exports both.
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
    task_advisories: list[dict[str, Any]]
    suggested_next_actions: list[SuggestedNextAction]


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
    inspection_next_action: SuggestedNextAction | None = None
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
class ProjectBriefGate:
    """A condition that blocks a class of action until deliberately cleared.

    State, not script: the gate names what is blocked and the one call that
    inspects it; the agent decides how to proceed.
    """

    gate: str
    blocks: str  # "mutation" | "export" | "none"
    detail: str
    details_call: str


@dataclass(frozen=True)
class ProjectBriefQueue:
    name: str
    count: int
    example_iri: str | None


@dataclass(frozen=True)
class ProjectBriefDataset:
    iri: str
    label: str | None
    is_table: bool
    status: str
    column_count: int
    caveat_count: int


@dataclass(frozen=True)
class ProjectBrief:
    key_counts: dict[str, int]
    dataset_count: int
    datasets: list[ProjectBriefDataset]
    gates: list[ProjectBriefGate]
    queues: list[ProjectBriefQueue]
    suggested_next_actions: list[SuggestedNextAction]
    limit: int


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
    validation_scope: str | None = None
    validation_conforms: bool | None = None
    validation_result_count: int = 0
    validation_results: list[ValidationDiagnostic] = field(default_factory=list)
    would_block_invalid_export: bool = False
    artifact_kind: str = "context_slice_trig"
    importable: bool = True
    recommended_import_tool: str | None = 'doxabase.import_bundle(kind="trig")'
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
    recommended_import_tool: str | None = (
        'doxabase.import_bundle(kind="revision_snapshots")'
    )
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
        'doxabase.import_bundle(kind="trig") then '
        'doxabase.import_bundle(kind="revision_snapshots")'
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
    snapshot_evidence: RevisionSnapshotEvidenceStatus | None = None
    snapshot_evidence_completeness: str = "unknown"
    blocking_preflight_actions: list[SuggestedNextAction] = field(
        default_factory=list
    )
    mutation_allowed_after: str = "direct_check_no_preflight"
    first_safe_next_action: RevisionNextAction | None = None


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
    tool: str | None
    args: dict[str, Any]
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
    mutation_allowed_after: str
    first_mutation_action: SuggestedNextAction | RevisionNextAction | None
    first_safe_review_or_mutation_action: (
        SuggestedNextAction | RevisionNextAction | None
    )
    first_safe_review_or_mutation_source: str | None
    blocking_preflight_actions: list[SuggestedNextAction]
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
    suggested_next_actions: list[SuggestedNextAction]
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
    "ProjectBriefGate",
    "ProjectBriefQueue",
    "ProjectBriefDataset",
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
]
