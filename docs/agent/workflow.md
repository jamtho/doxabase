# Agent Workflow

Use this sequence when arriving cold in a DoxaBase capsule.

1. Call `doxabase.list_docs`.
2. Read `overview`, `graph_roles`, `ontology_primer`, and `lexical_search` if you do not know the project conventions.
3. Call `doxabase.graph_overview` to inspect named graphs, counts, common classes, and predicates.
4. Call `doxabase.search` when you have a remembered term, caveat, column name, source note, or question-shaped keyword.
5. Call `doxabase.list_entities` for likely entry points, usually `type="rc:Table"` or `type="rc:Dataset"` in `graph="map"`.
6. Call `doxabase.describe_dataset` for a bounded view of one table's columns, layouts, caveats, provenance, and related datasets.
7. Use `doxabase.record_observation` when you discover a point-in-time finding that should remain available to later agents.
8. Use `doxabase.validate_graph` when you need an explicit SHACL diagnostic.

When adding future facts, choose graph roles by update pattern:

- Put vocabulary/model terms in `ontology`.
- Put consolidated current project knowledge in `map`.
- Put raw point-in-time findings in `observations`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL in `shapes`.

Do not write to `base_ontology` or `base_shapes`; they are immutable package seed graphs.

In the current V1 slice, the MCP interface does not yet expose graph revision or context-slice tools. Treat it as an inspection, validation, and fixture-loading surface.
It does expose lexical search and structured observation recording for routine findings.
