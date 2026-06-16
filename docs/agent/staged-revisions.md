# Staged Revisions

Use staged revisions when an agent wants to propose graph changes without
mutating the durable project map, ontology, observations, patterns, evidence, or
shapes yet.

Staging is not a demand for proof. It is a way to preserve a reviewable trace of
the agent's systematisation move: what it wants to add or remove, why that move
might be useful, how bold or conservative the move is, and whether the previewed
graph still validates.

## Stance

Set `stance` to describe the kind of thinking being captured:

- `rc:ExploratoryHunch`: a strong gestalt or promising framing that may not yet
  have tidy proof.
- `rc:CandidateRevision`: a proposal that seems ready for review as a graph
  change.
- `rc:ConservativeCleanup`: a mostly mechanical consistency or clarity change.
- `rc:AlternativeSystematisation`: one plausible framing among several.
- `rc:SupersededRevision`: a staged idea kept for memory but no longer preferred.

Rationale can be candid. It is fine to say that a proposed systematisation feels
more robust, explains more observed mess, or should generalise better under
future data, even if the evidence is not courtroom-grade.

## Tool Flow

Call `doxabase.stage_graph_revision` with Turtle payloads grouped as additions
and removals:

```python
result = stage_graph_revision_tool(
    db,
    summary="Treat messages as the map anchor",
    rationale=(
        "Exploratory hunch: this framing should make later joins easier to "
        "reason about as more message-like datasets arrive."
    ),
    stance="rc:ExploratoryHunch",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Messages a rc:Dataset, rc:Table ;
                    rdfs:label "Messages" .
            """,
        }
    ],
    validation_scope="all",
)
```

For a single `map` subject/predicate assertion, prefer
`doxabase.stage_map_assertion_change`. It calls `describe_assertion_support`,
generates the Turtle patch payloads, links related lore and anchors, and returns
the normal staged revision record alongside the support snapshot and a compact
`judgement_panel`. Read the panel first when deciding whether a single assertion
change is plausible: it brings current/proposed values, value-type context,
reasons the current value may be intentional, caveat scopes, strongest routes,
impact entries, and safety notes into one place. Use generic
`stage_graph_revision` when the patch is multi-resource, multi-graph, or cannot
be expressed as one assertion add/remove/replace.

Each patch must target one mutable graph role. The helper parses the RDF, rejects
empty or malformed payloads, previews additions/removals in memory, runs SHACL
validation over the preview scope, and records staged metadata in `history`.

The target graph is not changed when a revision is staged. Staged revisions are
review objects until `doxabase.apply_staged_revision` applies one.

Use `doxabase.describe_staged_revision` to inspect patch payloads, stance,
validation status, structured validation result diagnostics, support links, and
before/after count previews. For simple single-assertion `map` changes that
still replay cleanly, it also returns `judgement_panel`, the same compact review
surface used by `stage_map_assertion_change`. It also returns `impacts`:
deterministic review context for consequences such as caveat removals,
physical/value type changes, row-semantics changes, grouping changes, and
layout/path changes. Treat impacts as a spotlight, not a judge. They exist to
show linked observations, claims,
patterns, evidence, and revisions that may explain why a map assertion or caveat
was there. They do not make the proposal invalid by themselves.

Use `doxabase.export_staged_revision` to write a Markdown review bundle for one
proposal. For simple single-assertion `map` changes that still replay cleanly,
the export includes a `Judgement Panel` section so human and agent reviewers can
see the same compact values, value-type context, caveats, routes, and safety
notes that the JSON helper returned. Use `doxabase.export_staged_revisions` when
several alternatives, failed candidates, and repaired candidates should be
reviewed together.

## Systematisation Drafts

Call `doxabase.stage_systematisation` when you have a modelling hunch and want
to preserve one or more possible RDF framings for it. This helper is deliberately
not a promotion wizard. It does not choose the ontology shape for you; it packages
caller-authored RDF framings as staged revisions, validates them, and links later
framings as alternatives to the first by default. When several framings need the
same provisional vocabulary or assumptions, pass `shared_additions` or
`shared_removals`; those shared patches are included in each framing preview and
exported as `rc:SharedContextPatch` entries. Shared patches can target
`ontology`, `shapes`, or other mutable graph roles. Staged `shapes` patches
participate in the preview SHACL validation for each framing.

Use it for the part of the work where graph judgement matters:

- a pattern-first framing versus an ontology-first framing;
- a bold hunch that needs a new project vocabulary term;
- several plausible map shapes where one feels more robust but the reason is not
  yet fully mechanical;
- a conservative candidate plus a more speculative alternative.

Each framing can use the shorthand `graph` + `content` for one addition, or full
`additions` / `removals` patch lists when the graph move is more complex.
Add `review_note` and `review_recommendation` when the comparison itself needs
human-readable judgement, for example "preferred for now", "too bold but
informative", or "keep as a concrete alternative". These fields are not proof
and they do not apply the revision by themselves; they are review cues preserved
with the staged proposal.
Shared context patches are previewed before each framing's own patches:

```python
result = stage_systematisation_tool(
    db,
    summary="Explore identity-ladder modelling",
    intent=(
        "Keep two RDF framings alive while deciding whether this belongs in "
        "project vocabulary or as a pattern first."
    ),
    anchors=["ex:Messages", "ex:observation-123"],
    rationale=(
        "The concept may explain repeated identity hints better than a single "
        "fixed key model."
    ),
    shared_context_summary=(
        "Define provisional identity-ladder vocabulary so multiple framings can "
        "refer to the same tentative concept."
    ),
    shared_additions=[
        {
            "graph": "ontology",
            "content": "... Turtle defining ex:IdentityLadder ...",
        },
    ],
    framings=[
        {
            "label": "Deeper pattern hunch",
            "graph": "patterns",
            "content": "... Turtle defining an rc:Pattern ...",
            "review_note": "Keeps the strong hunch alive without forcing the map.",
            "review_recommendation": "Preferred for now.",
        },
        {
            "label": "Concrete map candidate",
            "graph": "map",
            "content": "... Turtle using the shared vocabulary ...",
            "stance": "rc:CandidateRevision",
            "review_recommendation": "Useful alternative, but wait for more support.",
        },
    ],
    validation_scope="all",
)
```

After staging several framings, export them together for review:

```python
db.export_staged_revisions(
    [revision.revision_iri for revision in result.staged_revisions],
    "/tmp/systematisation-review.md",
    title="Identity ladder alternatives",
    executive_summary=(
        "Prefer the pattern-first framing for now, while keeping the map "
        "candidate as useful pressure on the model."
    ),
)
```

The staged revision rationale records the systematisation intent, anchors,
overall rationale, shared-context summary, and framing-specific rationale. The
grouped export also surfaces review notes, recommendations, and diagnostic
headlines in its top sections so a reviewer can understand the semantic delta
without reading every Turtle payload first.

Systematisation anchors are also recorded as `rc:revisionAnchor` triples on each
staged revision. Use anchors for resources the hunch is about, such as columns,
tables, caveats, relationships, observations, or patterns. Do not use anchors as
a substitute for evidence: supporting observations, claims, patterns, and
evidence links still carry the justification for the proposal.

## Pattern-Supported Promotion

Call `doxabase.stage_pattern_promotion` when one or more existing patterns are
the reason a graph change now seems worth staging. This is a pattern-aware
wrapper over `stage_systematisation`, not an automatic map editor. Pass the
pattern IRIs and caller-authored framings. The helper:

- records the selected patterns as `supporting_patterns`;
- rolls up their supporting observations, claims, and evidence into revision
  metadata;
- uses the pattern IRIs, pattern targets, and `rc:mapImplication` resources as
  revision anchors;
- delegates patch parsing, preview counts, validation, alternatives, and review
  notes to the ordinary staged systematisation flow.

Use it when a pattern supports a caveat, relationship, project vocabulary term,
shape, or other durable structure but the exact graph move still deserves review.

## Applying Staged Revisions

Use `doxabase.apply_staged_revision` after reviewing a staged revision and
deciding it should become durable graph state. The helper is intentionally
conservative:

- it rejects a staged revision that already has an applied-revision event;
- it checks patches in recorded `patchSequence` order and compares each target
  graph count against the recorded `beforeTripleCount`;
- it previews all patches in memory and reruns validation before mutating graph
  state;
- it applies additions/removals only after those checks pass;
- it records an `rc:AppliedStagedRevision` history event linked back with
  `rc:appliesStagedRevision`.

Use `doxabase.check_staged_revision_apply` first when you want a read-only
answer. It reports whether the staged revision has already been applied, whether
any patch target graph has drifted from its recorded `beforeTripleCount`, the
preview count for each patch, preview validation diagnostics, `status`,
`summary`, and structured `suggested_next_actions`. Read `status` and `summary`
first. Current statuses are `ready`, `already_applied`, `conflict`,
`validation_failed`, and `not_ready`.

This is not a full merge system. A harmless unrelated graph change can still
show up as a conflict because the first guard is count-based. In that case,
restage the patch against current graph state rather than forcing it through.

## What Gets Recorded

Staged revisions are `rc:GraphRevision` resources with `rc:StagedRevision` type,
optional support links to observations, claims, patterns, and evidence, optional
`rc:revisionAnchor` topical links, optional linked `sh:ValidationResult`
diagnostics, plus one or more `rc:GraphPatch` resources.

Patch entries record:

- `rc:patchOperation`: addition or removal;
- `rc:targetGraph`: the mutable graph role;
- `rc:patchFormat` and `rc:patchContent`;
- `rc:patchRole`: `rc:SharedContextPatch` or `rc:FramingPatch`;
- `rc:patchSequence`: one-based preview/check/apply order;
- `rc:patchTripleCount`;
- `rc:beforeTripleCount` and `rc:afterTripleCount` for the preview sequence.

Use `alternative_to` when recording competing staged systematisations. Keeping
alternatives side by side is expected; staged revisions are cheap memory for
creative exploration, not a forced march toward one approved answer.

## Validation Notes

DoxaBase runs pySHACL with RDFS inference during preview validation. That is
usually helpful because ordinary RDF vocabulary such as `rdfs:range` can teach
the validator useful class context. It also means a shape using `sh:class` may
pass because the class was inferred rather than explicitly written. When a trial
needs a stricter check, add shape constraints for the concrete property,
node-kind, count, or value that should be present.

When validation fails, staged revisions preserve structured SHACL diagnostics in
`validation_results`. Read these before guessing from patch text. Each result
can include focus node, result path, source constraint component, severity,
value, and one or more messages. Markdown staged-revision exports include the
same diagnostics before the patch payloads.

## Repair Loop Example

A useful staged-validation loop is:

1. Record the lore first as observations, claims, or patterns.
2. Stage shared provisional ontology and shapes for the hunch.
3. Let a candidate fail if it is incomplete.
4. Inspect `describe_staged_revision(...).validation_results`.
5. Stage a repaired candidate using the diagnostic focus node, result path, and
   message.
6. Keep a pattern-first or bolder alternative if the deeper hunch should not be
   collapsed into the conservative map candidate.

For example, a Polymarket trial treated `outcomes` and `clobTokenIds` as
parallel JSON arrays that bridge Gamma market snapshots to scalar CLOB token
identifiers. The agent first recorded claims and a pattern saying this was a
positional array bridge, not a plain foreign key. It then staged shared
provisional vocabulary and a shape requiring each `OutcomeTokenAlignment` to
name the market table, condition column, outcome-label array column, CLOB
token-id array column, downstream token columns, and alignment basis.

The first map candidate intentionally omitted the token-id array column. Its
staged revision failed with a diagnostic like:

```text
focus_node: ft:outcome_token_alignment_v1
result_path: ft:clobTokenIdArrayColumn
constraint: sh:MinCountConstraintComponent
message: Outcome token alignments must name the CLOB token-id array column.
```

The repair was then a graph move rather than guesswork: add
`ft:clobTokenIdArrayColumn pm:mkt_clob_token_ids` to that same focus node and
stage a new candidate. A third framing kept the more conceptual hunch alive as
a pattern-first latent outcome-slot model. This is the intended feel of the
workflow: validation is a guide for graph repair, while alternatives preserve
creative modelling space.

## Awkward Concept Test

Promotion helpers should be tested against ideas that do not fit neatly into the
current ontology. A good helper should let an agent say, in effect:

- this may need a new project vocabulary term;
- this may belong in `ontology` before it belongs in `map`;
- this is a useful intermediate concept even if no existing helper shape covers
  it;
- here are several plausible RDF framings, and this one feels more robust.

If a promotion helper can only produce familiar map facts, it is too narrow. The
agent's knowledge-graph reasoning should remain primary; DoxaBase should help
draft, validate, and preserve the graph move, not decide that only existing
templates are legitimate.

## Limits

DoxaBase can apply one staged revision with conservative count-based conflict
checks. It does not yet support rich conflict diagnostics, rebasing, approval
state machines, or durable graph version storage. Restage proposals when the
target graph has drifted.
