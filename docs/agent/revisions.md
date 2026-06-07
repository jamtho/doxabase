# Revision History

Use the `history` graph to record why graph state changed, what graph roles
changed, what graph roles were included for review, and where a reviewer can
inspect the resulting bundle.

Use `doxabase.record_graph_revision` after graph state has changed, after an
import/export, or after a review bundle when the rationale should remain
available to later agents. For proposed additions/removals that should not be
applied yet, use `doxabase.stage_graph_revision`; see `staged_revisions`.

## When To Record

Record a graph revision when you can say:

- these graph roles changed or were consolidated;
- these graph roles were included in the review/export context;
- this is why the change was made;
- these observations, claims, patterns, or evidence supported it;
- this validation result or export path helps a future reviewer.

Do not use ordinary revision records for `base_ontology` or `base_shapes`.
Changes to shipped seed graphs are package migrations, not project edits.

## Example

```python
validation = db.validate_graph(scope="all")
export = db.export_trig("/tmp/project-review.trig")

db.record_graph_revision(
    summary="Project review bundle exported",
    rationale="The map helper field trial produced current-best map facts and supporting observations.",
    changed_graphs=["map", "observations", "patterns", "evidence"],
    included_graphs=export.graphs,
    revision_type="rc:ExportRevision",
    supporting_patterns=[
        "https://example.test/project#pattern_doc_id_parent_doc_id_spine",
    ],
    export_path=export.path,
    graph_counts=export.graph_counts,
    validation_scope=validation.scope,
    validation_conforms=validation.conforms,
    validation_result_count=validation.result_count,
)
```

If an agent records new observations or patterns but leaves the map unchanged,
keep `changed_graphs` narrow and include the map only as review context:

```python
export = db.export_trig("/tmp/project-review.trig", graphs="workflow")

db.record_graph_revision(
    summary="No-map-edit review bundle exported",
    rationale="The map was exported for reviewer context, but only observations, patterns, and evidence changed.",
    changed_graphs=["observations", "patterns", "evidence"],
    included_graphs=export.graphs,
    revision_type="rc:FieldTrialRevision",
    export_path=export.path,
    graph_counts=export.graph_counts,
)
```

When `graph_counts` is supplied, DoxyBase also records those graph roles as
included review/snapshot context. Passing `included_graphs=export.graphs` makes
that distinction explicit for readers.

`changed_graphs` describes the content change being recorded. It should not
include `history` merely because `record_graph_revision()` writes revision
metadata there.

Use `describe_graph_revision()` when you want a compact review of a revision
record instead of generic outgoing triples.

## Revision Types

Common revision type IRIs:

- `rc:ManualRevision`
- `rc:ImportRevision`
- `rc:ExportRevision`
- `rc:MapAuthoringRevision`
- `rc:FieldTrialRevision`

Use project-specific revision types if these are too coarse. Declare custom
revision types as `rc:RevisionType` resources in project ontology before relying
on `validate_graph(scope="all")`.

## Staged Proposals

`doxabase.stage_graph_revision` records reviewable patch payloads in `history`
without mutating the target graph. Use it when an agent has a promising hunch,
an alternative systematisation, or a candidate map change that should be
preserved for review before it becomes current-best context.

Staged revisions are deliberately lighter than an approval process. They record
stance, rationale, support links, Turtle additions/removals, preview counts, and
SHACL validation results. They do not require proof before an agent can preserve
a bold idea.

Use `describe_staged_revision()` to inspect the proposal and
`export_staged_revision()` to write a Markdown review bundle.

## Limits

DoxaBase can record staged patch proposals, but it does not yet apply them,
detect conflicts, or store durable graph versions. The revision helpers preserve
rationale and review context now, while leaving approval, promotion, and full
slice replacement for later.
