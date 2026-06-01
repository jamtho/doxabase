# Graph Roles

DoxaBase uses named graph roles to separate stable vocabulary, project facts,
observations, patterns, evidence, and validation shapes.

## Immutable Seed Graphs

`base_ontology`

The shipped Rich Canopy `rc:` vocabulary loaded from `ontology/rc_core.ttl`. Do not write project-specific terms here.

`base_shapes`

The shipped open SHACL shapes loaded from `ontology/rc_shapes.ttl`. Do not write project-specific shapes here.

## Mutable Project Graphs

`ontology`

Project-owned vocabulary and model layer: client classes, properties, value types, SKOS concepts, labels, comments, definitions, and term deprecations.

`map`

The current best structured map of the project/data world: datasets, tables, columns, accepted joins, caveats, computability claims, current summaries, and links from project entities to ontology terms.

`observations`

Point-in-time or tentative findings: profiling results, observed counts, candidate joins, raw notes, failed assumptions, exploratory discoveries, and agent-run observations.
Use `record_observation()` for routine structured observation writes.

`patterns`

Syntheses over observations, claims, or evidence. Patterns explain why related
findings belong together and how they may support the current map, without
requiring an immediate map edit.
Use `record_pattern()` for routine pattern writes.

`evidence`

Support for observations, patterns, or map assertions: source files, query text, URLs, hashes, evidence summaries, validation reports, and samples.
`record_observation()` can create a linked evidence resource when evidence fields are supplied.

`shapes`

Project-owned SHACL shapes. These extend `base_shapes` and remain open unless a project deliberately chooses stricter validation.

`history`

Graph versions, revision rationale, diffs, superseded terms, deprecated mappings, and consolidation notes. This is mostly reserved in the current implementation.

## Logical Includes

For retrieval and validation, `ontology` means `base_ontology + ontology`, and `shapes` means `base_shapes + shapes`.
