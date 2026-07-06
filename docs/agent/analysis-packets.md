# Analysis Packets

Use `record_map_fact(kind="analysis_packet")` when an external analysis pass
has already produced reviewed logical populations, aggregate artifact
locators, visual outputs, reusable query recipes, caveats, or follow-up
tasks, and the next agent needs one graph-native handoff node.

The helper is deliberately no-I/O and locator-only: it records paths,
artifact metadata, view links, recipe text, and task text. It does not read
files, parse Markdown, store image bytes, preserve raw rows, or decide
whether an analysis is valid. The whole packet is preflighted on a scratch
capsule before writing, so an invalid view or task leaves nothing behind.

## What A Packet Records

The packet lands in `evidence` as both `rc:Evidence` and
`rc:AnalysisPacket`: required `iri` and `summary`, plus at least one
`evidence_sources` value or one artifact `source_path`. Optionally:

- `analysis_views` — reviewed logical view specs (same structured fields as
  `record_map_fact(kind="analysis_view")`: description, source datasets,
  denominator, caveat IRIs — existing `rc:KnownCaveat` resources, not inline
  prose — and query snippets), or `analysis_view_iris` for views already in
  the capsule.
- `artifacts` — `rc:AnalysisArtifact` evidence rows with source locators,
  roles, media types, hashes, byte sizes, image dimensions, support links.
- `query_recipes` — `rc:ExecutableQuerySnippet` cookbook entries that are
  not themselves analysis populations.
- `followup_tasks` — `rc:AnalysisFollowupTask` rows with text, priority,
  targets.
- pattern fields — one packet-supported `record_pattern` synthesis.

The `mcp_tools` doc lists the exact spec fields.

## Choosing The Door

- One durable handoff node across populations, recipes, artifacts, and
  tasks → `kind="analysis_packet"`.
- Only logical views → `kind="analysis_view"` (one) or
  `kind="analysis_view_bundle"` (several per call; a bulk write, not a
  grouping resource).
- A reviewed table/profile ingestion sidecar → `kind="profile_manifest"`
  (see `profiling`).
- A single executed query attempt or failure →
  `record_observation(kind="query_result")`.

## The Reviewed JSON Adapter

When a reviewed packet lives on disk, use the CLI instead of a one-off
script (format `doxabase.analysis_packet_manifest.v1`):

```bash
python -m doxabase.analysis_packet --capsule capsule.sqlite \
  --manifest analysis-packet.json
```

For a directory of sidecar files, scaffold first: `--init-manifest
--sidecar-dir DIR --packet-iri IRI --summary ... --output packet.json`
enumerates artifact locators (media type, byte size, dimensions;
`--hash-artifacts` adds content hashes). `--extract-markdown-views` seeds
review-only candidate views from fenced `CREATE VIEW` SQL blocks. Scaffolds
are skeletons: the apply path rejects `TODO:` placeholders by default —
translate the reviewed denominators, SQL, caveats, and tasks into structured
fields before applying (`--allow-review-placeholders` is for mechanics-only
scratch tests).

Markdown sidecars remain locator evidence until someone does that
translation: searchable, but invisible to `project_brief` packet/view/recipe
counts. Graph-native handoff means a reviewed manifest applied to the
capsule, then nonzero packet/view/snippet counts verified before
re-exporting.

## Reading A Packet

Packets surface in `project_brief` key counts and queues. Seed
`get_context_graph(seed_iris=[packet_iri], profile="resource_brief")` for
the bounded handoff: view, recipe, and task links are ranked ahead of
artifact bulk when a large packet exceeds the route cap
(`describe_resource` paging covers exhaustive artifact review). Inspect
linked views with `describe_resource` (analysis views are auto-detected) —
caveats attached to a parent/source view are reported as source caveats on
children; repeat a caveat on a child view only when the child owns it.
