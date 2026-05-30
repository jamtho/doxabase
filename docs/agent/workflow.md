# Agent Workflow

Use this sequence when arriving cold in a DoxyBase capsule.

1. Call `doxybase.list_docs`.
2. Read `overview`, `graph_roles`, and `ontology_primer` if you do not know the project conventions.
3. Call `doxybase.graph_overview` to inspect named graphs, counts, common classes, and predicates.
4. Call `doxybase.list_entities` for likely entry points, usually `type="rc:Table"` or `type="rc:Dataset"` in `graph="map"`.
5. Use `doxybase.validate_graph` when you need an explicit SHACL diagnostic.

When adding future facts, choose graph roles by update pattern:

- Put vocabulary/model terms in `ontology`.
- Put consolidated current project knowledge in `map`.
- Put raw point-in-time findings in `observations`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL in `shapes`.

Do not write to `base_ontology` or `base_shapes`; they are immutable package seed graphs.

In the current V1 slice, the MCP interface does not yet expose graph revision or context-slice tools. Treat it as an inspection, validation, and fixture-loading surface.
