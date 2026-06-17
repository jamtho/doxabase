# Revision History

Use the `history` graph to record why graph state changed, what graph roles
changed, what graph roles were included for review, and where a reviewer can
inspect the resulting bundle.

Use `doxabase.record_graph_revision` after graph state has changed, after an
import/export, or after a review bundle when the rationale should remain
available to later agents. For proposed additions/removals that should be
reviewed before application, use `doxabase.stage_graph_revision`; see
`staged_revisions`.

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

When `graph_counts` is supplied, DoxaBase also records those graph roles as
included review/snapshot context. Passing `included_graphs=export.graphs` makes
that distinction explicit for readers.

`changed_graphs` describes the content change being recorded. It should not
include `history` merely because `record_graph_revision()` writes revision
metadata there.

Use `list_graph_revisions()` when you need to discover staged, applied, or
historical revision records. Use `describe_graph_revision()` when you want a
compact review of one revision record instead of generic outgoing triples.
Graph snapshots include both `triple_count` and a `sha256:<hex>` content digest;
matching counts alone do not prove two revision contexts are identical.

## Revision List Triage

When reviewing unknown or possibly stale staged proposals, start with the list
row before opening the full staged revision:

```python
staged = db.stage_graph_revision(
    summary="Add trial dataset",
    rationale="Keep this proposal reviewable before making it current-best map context.",
    stance="rc:CandidateRevision",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:TrialDataset a rc:Dataset, rc:Table ;
                    rdfs:label "Trial dataset" .
            """,
        }
    ],
    validation_scope="all",
)

before = db.list_graph_revisions(include_apply_checks=True)

# Any ordinary map write can make an older staged snapshot stale.
db.record_map_dataset(
    iri="https://example.test/project#InterveningDataset",
    label="Intervening dataset",
    is_table=True,
)

after = db.list_graph_revisions(include_apply_checks=True)
```

Read `application_status`, `application_decision`, `application_can_apply`,
`application_summary`, `application_blocking_reasons`, and
`suggested_next_calls` first. They tell you whether the staged proposal is ready
for review, already applied, blocked by graph drift, or needs fuller inspection.
The default list call uses `drift_detail="summary"` so snapshot drift rows carry
counts and digests without large exact changed-triple arrays. Then use
`describe_staged_revision()`, `check_staged_revision_apply()`,
`list_graph_revisions(drift_detail="exact")`, or an export helper when you need
patch details, exact drift triples, validation diagnostics, or a human review
bundle.

A staged patch can be blocked even when its own triples are still absent from the
target graph. DoxaBase applies staged revisions conservatively: unrelated count
or digest drift means the target graph is no longer the same graph state the
proposal was previewed against, so restage or inspect before applying.

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

DoxaBase can apply staged patch proposals with conservative graph-state conflict
checks, and can restage a stale proposal against current graph state when
unrelated drift made it obsolete. New staged revisions store snapshot rows for
exact count/digest drift reporting, but DoxaBase does not yet provide rich
semantic merge diagnostics, approval workflows, or durable graph version
browsing beyond those staged snapshots. The revision helpers preserve rationale
and review context now, while leaving fuller slice replacement for later.
