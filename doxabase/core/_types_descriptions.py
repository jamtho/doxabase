"""Dataset, query, profile, map, slice, and search description types.

Mechanically split from doxabase.core._types; classes are verbatim and
order-preserved. Part 2 of 2; ``doxabase.core._types`` re-exports both.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types_revisions import *  # noqa: F401,F403

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
    required_binding_details: list[dict[str, Any]] = field(default_factory=list, metadata={"doxabase_internal": True})
    binding_example: str | None = field(default=None, metadata={"doxabase_internal": True})
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
    columns: list[ColumnDescription] = field(metadata={"doxabase_internal": True})
    path_templates: list[str]
    query_target_decision: QueryTargetDecision
    query_target_candidates: list[QueryTargetCandidate]
    ready_candidate_indexes: list[int]
    unselected_ready_candidate_indexes: list[int]
    direct_clean_candidate_indexes: list[int]
    unselected_direct_clean_candidate_indexes: list[int]
    physical_layouts: list[PhysicalLayoutDescription]
    storage_accesses: list[StorageAccessDescription]
    partition_schemes: list[PartitionDescription] = field(metadata={"doxabase_internal": True})
    caveats: list[CaveatDescription]
    upstream_caveats: list[CaveatDescription] = field(metadata={"doxabase_internal": True})
    suggested_next_actions: list[SuggestedNextAction]
    safe_inspection_action_indexes: list[int]
    first_safe_inspection_action_index: int | None


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
    primary_repair_tool: str | None = None
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


@dataclass(frozen=True)
class AnalysisViewBundleRecord:
    records: list[MapResourceRecord]
    analysis_views: list[AnalysisViewDescription]
    view_iris: list[str]
    view_count: int
    query_snippet_count: int
    suggested_next_actions: list[SuggestedNextAction]


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
    pending_staged_promotion_iris: list[str] = field(default_factory=list)
    pending_staged_promotion_count: int = 0
    pending_staged_assertion_iris: list[str] = field(default_factory=list)
    pending_staged_assertion_count: int = 0
    duplicate_group_key: str = ""
    duplicate_count: int = 1
    duplicate_advisory_indexes: list[int] = field(default_factory=list)
    duplicate_profile_observation_iris: list[str] = field(default_factory=list)


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
    note: str


@dataclass(frozen=True)
class ProfileFollowthroughActionResolution:
    action_group: str
    action_index: int
    tool: str
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
    revision_checks: list[ProfileFollowthroughRevisionCheck]
    revision_check_count: int
    restage_stale_revisions: bool
    restaged_revision_iris: list[str]
    suggested_next_actions: list[SuggestedNextAction]
    suggested_next_action_groups: dict[str, list[SuggestedNextAction]]
    profile_type_assertion_batch_plan: dict[str, Any]
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
    suggested_next_action_groups: dict[str, list[SuggestedNextAction]]
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
    type_advisories: list[ProfileTypeFindingAdvisory]
    type_advisory_count: int
    type_advisory_status_counts: dict[str, int]
    type_review_required: bool
    type_advisory_suggested_next_actions: list[SuggestedNextAction]
    revision_iri: str | None
    staged_revision: StagedGraphRevisionRecord | None
    suggested_next_actions: list[SuggestedNextAction]
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
    related_datasets: list[RelatedDatasetDescription] = field(metadata={"doxabase_internal": True})
    related_dataset_groups: list[RelatedDatasetGroup] = field(metadata={"doxabase_internal": True})
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
    tool: str
    args: dict[str, Any]
    reason: str


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
    route_label: str = field(metadata={"doxabase_internal": True})
    source_iri: str | None = None
    source_label: str | None = field(
        default=None, metadata={"doxabase_internal": True}
    )
    depth: int = 0


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
    routes: list[ContextSliceRoute] = field(metadata={"doxabase_internal": True})


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
