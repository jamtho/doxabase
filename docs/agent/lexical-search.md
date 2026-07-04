# Lexical Search

`doxabase.search` makes captured lore cheap to rediscover. Agents rarely
arrive knowing the right IRI, graph role, or predicate; search is the
low-friction way to ask "have we already noticed something about this?"

## What It Does

V1 search is FTS over literal RDF objects in the quad store — labels,
comments, summaries, caveat and source descriptions, column names, path
templates, storage roots, evidence source strings. The index is derivative
and rebuilt from the quads after writes; the RDF stays the source of truth.
It is not embedding search, SPARQL, or graph expansion, and it is not
type-aware — to browse by RDF class, use `list_entities(type="rc:Pattern")`
(or `rc:Claim`, `rc:Evidence`, ...) and then `describe_resource`.

Matches are resources, not detached snippets: graph role, IRI or blank node,
label, RDF types, matched predicate, matched text, highlighted snippet.
A match is candidate context — it says a claim exists, not that it is
current, complete, or applicable.

## Scopes And Graph Scoping

- `scope="graphs"` (default) searches literal claims across named graphs.
  `graph=` narrows to one role: `map` for consolidated knowledge,
  `observations`, `patterns`, `evidence`, `ontology` (which includes
  `base_ontology`), or `None` for everything.
- `scope="staged_patches"` searches staged revision patch payloads (`graph`
  defaults to history there; `current_staged_work_only` defaults true).
  Use it when you remember staged-only prose, a proposed ontology label, or
  an IRI local name that describers cannot see because the proposal was
  never applied.

Unscoped search is seed-heavy for generic data words ("storage", "row
count") because base ontology and shape text are indexed too; the response
flags seed-heavy pages and suggests scoped retries — follow them (usually
`graph="map"`) before deciding project facts are absent.

## Query Technique

Multi-token queries first require all tokens in one literal, then fall back
to local co-mentions (resources in the same immediate context whose literals
collectively cover the query — useful for same-table column discovery).
When expected lore does not appear, retry before concluding absence: shorter
phrases, exact labels or column names, distinctive stored words. A natural
sentence ("permit_number joins inspection events") can miss a pattern whose
stored wording differs; "inspection events permit_number" can find it.

Zero-match responses include recovery suggestions (scoped retries, entity
browsing, staged-payload search). They are routes, not evidence the fact
exists.

## After A Match

Inspect with the most specific tool: `describe_dataset` for tables,
`describe_resource` for anything (patterns and analysis views are
auto-detected), `get_context_graph(profile="pattern_brief")` when a found
pattern should hand off its whole support chain. Search is a memory
retrieval affordance, not a semantic judge — the agent still supplies the
judgement.
