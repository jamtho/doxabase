# Response Conventions

The rules every DoxaBase MCP response follows. Learn these once; then trust
the per-tool schemas for field lists. (The older `response_shapes` document
predates these conventions and is being retired; where they disagree, this
document wins.)

## The envelope

- **Absent, null, and empty are equivalent.** Responses omit fields whose
  value is `null`, `[]`, or `{}`. Never distinguish "key missing" from
  "key null"; read with `.get(...)`-style tolerance. Falsy scalars (`0`,
  `false`, `""`) are always real values and always present.
- **Graph content travels as TriG**, in a `trig` string field. JSON never
  carries per-triple objects; counts summarize, TriG carries. Parse it as
  RDF when you need exact statements; read counts when you don't.
- Responses are plain JSON: objects, arrays, strings, numbers, booleans.

## Truncation and limits

Every list that can be limited reports the same family of fields where
relevant: a `count` (returned), `total_count` or `candidate_*_count`
(available), `omitted_count` (difference), `has_more`/`next_offset`
(paging), and a `truncated` flag with `truncation_scope` where a whole
response can be cut. A limit you pass is echoed back. If `omitted_count`
is positive and the omitted part matters, rerun with a higher limit —
responses never silently drop content without reporting it.

## Suggestions

`suggested_next_actions` entries have exactly three fields: `tool` (the
MCP tool name to call), `args` (the arguments to call it with —
placeholder values are UPPERCASE or angle-bracketed and must be replaced
with reviewed values, never passed through), and `reason` (one sentence
of why).

Suggestions are hints from mechanics, not instructions: the capsule cannot
see your task. Prefer your own judgement about what to do next; see the
`working_the_capsule` doc for how gates and queues should shape that
judgement.

## Sizes are guaranteed

Response sizes on the standard fixture capsule are budget-tested
(`tools/scoreboard.py`); a response that would flood your context is a bug,
not a cost you must plan around. Orientation calls are cheap to repeat.

## Errors

Errors name the field and the constraint ("relationship column
source_columns[0] must be a column IRI; got 'body'"), including joint
constraints between optional parameters. An error is always safe: nothing
was written.

## Privacy posture

Export-shaped responses carry `privacy_warnings`, match counts, and a
`scanner_note`. Scanner-clean means "no credential-shaped literals
matched"; it is a review prompt, never export approval. Secret values are
never echoed in warnings or matches.
