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

Each patch must target one mutable graph role. The helper parses the RDF, rejects
empty or malformed payloads, previews additions/removals in memory, runs SHACL
validation over the preview scope, and records staged metadata in `history`.

The target graph is not changed. Staged revisions are review objects.

Use `doxabase.describe_staged_revision` to inspect patch payloads, stance,
validation status, support links, and before/after count previews. Use
`doxabase.export_staged_revision` to write a Markdown review bundle.

## Systematisation Drafts

Call `doxabase.stage_systematisation` when you have a modelling hunch and want
to preserve one or more possible RDF framings for it. This helper is deliberately
not a promotion wizard. It does not choose the ontology shape for you; it packages
caller-authored RDF framings as staged revisions, validates them, and links later
framings as alternatives to the first by default.

Use it for the part of the work where graph judgement matters:

- a pattern-first framing versus an ontology-first framing;
- a bold hunch that needs a new project vocabulary term;
- several plausible map shapes where one feels more robust but the reason is not
  yet fully mechanical;
- a conservative candidate plus a more speculative alternative.

Each framing can use the shorthand `graph` + `content` for one addition, or full
`additions` / `removals` patch lists when the graph move is more complex:

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
    framings=[
        {
            "label": "Project vocabulary term",
            "graph": "ontology",
            "content": "... Turtle defining ex:IdentityLadder ...",
            "stance": "rc:AlternativeSystematisation",
        },
        {
            "label": "Pattern first",
            "graph": "patterns",
            "content": "... Turtle defining an rc:Pattern ...",
        },
    ],
    validation_scope="all",
)
```

The staged revision rationale records the systematisation intent, anchors,
overall rationale, and framing-specific rationale. This keeps exports readable
even while richer promotion metadata is still evolving.

Systematisation anchors are also recorded as `rc:revisionAnchor` triples on each
staged revision. Use anchors for resources the hunch is about, such as columns,
tables, caveats, relationships, observations, or patterns. Do not use anchors as
a substitute for evidence: supporting observations, claims, patterns, and
evidence links still carry the justification for the proposal.

## What Gets Recorded

Staged revisions are `rc:GraphRevision` resources with `rc:StagedRevision` type,
optional support links to observations, claims, patterns, and evidence, optional
`rc:revisionAnchor` topical links, plus one or more `rc:GraphPatch` resources.

Patch entries record:

- `rc:patchOperation`: addition or removal;
- `rc:targetGraph`: the mutable graph role;
- `rc:patchFormat` and `rc:patchContent`;
- `rc:patchTripleCount`;
- `rc:beforeTripleCount` and `rc:afterTripleCount` for the preview sequence.

Use `alternative_to` when recording competing staged systematisations. Keeping
alternatives side by side is expected; staged revisions are cheap memory for
creative exploration, not a forced march toward one approved answer.

## Awkward Concept Test

Future promotion helpers should be tested against ideas that do not fit neatly
into the current ontology. A good helper should let an agent say, in effect:

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

DoxaBase does not yet apply staged revisions. There is no conflict detection,
approval state machine, or durable graph version storage. For now, staged
revisions are reviewable proposals with validation previews and exportable patch
payloads. Apply/promote workflows can build on this surface later.
