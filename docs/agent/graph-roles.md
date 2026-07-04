# Graph Roles

DoxaBase separates knowledge by named graph role. Choose the role by how the
fact will be updated and trusted, not by where it was discovered.

## Immutable Seed Graphs

- `base_ontology` — the shipped Rich Canopy `rc:` vocabulary
  (`ontology/rc_core.ttl`). Never write project terms here.
- `base_shapes` — the shipped open SHACL shapes (`ontology/rc_shapes.ttl`).
  Never write project shapes here.

## Mutable Project Graphs

- `ontology` — project-owned vocabulary and model terms: classes, properties,
  value types, metric kinds, labels, definitions, deprecations.
- `map` — the current best structured map of the project's data world:
  datasets, tables, columns, accepted joins, caveats, storage access, physical
  layout, and links to ontology terms. Routine writes go through
  `record_map_fact` (kind-dispatched); reviewed changes to existing map facts
  go through `stage_revision` then `apply_staged_revision`.
- `observations` — point-in-time or tentative findings: profile results,
  observed counts, candidate joins, failed assumptions, query outcomes.
  Routine writes: `record_observation` (kinds `observation`, `profile`,
  `claim`, `query_result`) and `record_profile`.
- `patterns` — syntheses over related observations, claims, or evidence,
  written with `record_pattern`. Patterns explain why findings belong together
  without requiring an immediate map edit.
- `evidence` — support for everything else: source files, query text, URLs,
  hashes, samples, source spans. Recording helpers create linked evidence
  when evidence fields are supplied.
- `shapes` — project-owned SHACL extensions of `base_shapes`.
- `history` — revision rationale, staged patch payloads, applied-revision
  events, graph snapshots, review-bundle metadata. Written by
  `record_graph_revision`, `stage_revision`, and `apply_staged_revision`.

## Logical Includes

For retrieval and validation, `ontology` means `base_ontology + ontology`,
and `shapes` means `base_shapes + shapes`.

## Placement Cues

- A fact future agents should start from → `map`.
- A fact true on a date, from a sample, or not yet trusted → `observations`.
- The reasoning that connects findings → `patterns`.
- How you know → `evidence`.
- What a term means → `ontology`; what must hold → `shapes`.
- Why the graph changed → `history` (never a staged patch target: patches
  target the other mutable roles, and their metadata lands in `history`
  automatically).

Fixture graph IRIs under `https://richcanopy.org/graph/{role}` map onto these
roles on import.
