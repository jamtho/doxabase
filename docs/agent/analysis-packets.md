# Analysis Packets

Use `record_analysis_packet` when an external analysis pass has already
produced reviewed logical populations, aggregate artifact locators, visual
outputs, reusable query recipes, caveats, or follow-up tasks, and the next
agent needs one graph-native handoff node to inspect.

This helper is intentionally no-I/O and locator-only. It records paths,
artifact metadata, analysis-view links, query recipes, and task text, but it
does not read files, parse JSON or Markdown, store image bytes, preserve raw
rows, or decide whether an analysis is valid.

## What It Records

`record_analysis_packet` writes the packet itself as both `rc:Evidence` and
`rc:AnalysisPacket` in the `evidence` graph. The packet gets a required
`rc:summary`, optional label, `dcterms:source` literals from
`evidence_sources`, and links to any analysis views, artifacts, and follow-up
tasks.

The helper can also:

- create logical analysis views from `analysis_views`, using the same
  structured fields as `record_map_analysis_view_bundle`;
- link existing logical views from `analysis_view_iris`, which must already be
  recorded `rc:AnalysisView` resources unless the same call creates them;
- record `rc:AnalysisArtifact` evidence resources with source locators,
  roles, media types, hashes, byte sizes, image dimensions, and support links;
- record packet-level `query_recipes` as `rc:ExecutableQuerySnippet` resources
  for reusable cookbook snippets that are not themselves analysis
  populations;
- record `rc:AnalysisFollowupTask` resources with task text, priority, and
  target links;
- optionally create a `record_pattern` synthesis supported by the packet and
  targeted at the packet plus linked analysis views.

The call preflights the full structured packet on a scratch capsule before
writing to the live capsule, so a later invalid view, artifact, or task does
not leave earlier packet resources behind.

## Reviewed JSON Adapter

When a reviewed packet already lives on disk as JSON, use the CLI adapter
instead of writing a one-off `json.load` script:

```bash
python -m doxabase.analysis_packet \
  --capsule capsule.sqlite \
  --manifest analysis-packet.json
```

The manifest must use
`"format": "doxabase.analysis_packet_manifest.v1"` and the same packet fields
described below, with `packet_iri` accepted as an alias for `iri`. The command
applies the reviewed metadata, runs graph validation, and prints the packet,
view, artifact, recipe, task, and suggested follow-up handles as JSON. It does
not read referenced Markdown/JSON/PNG files, parse report text, store artifact
bytes, or execute query recipes.

For a maintained local smoke route, run
`python examples/analysis-packet-manifest-smoke.py`; it creates a reviewed
source table, writes a packet manifest with logical views, artifacts, query
recipes, and tasks, applies the manifest to the existing capsule, and inspects
the packet through context slices and logical-view query context.

## Inputs

Required fields:

- `iri`: the packet IRI;
- `summary`: the packet summary;
- at least one `evidence_sources` value or one artifact `source_path`.

Artifact specs accept:

- `iri` or `artifact_iri`, otherwise DoxaBase uses
  `{packet_iri}/artifact/{index}`;
- `source_path` or `path`;
- optional `label`, `summary`, `artifact_role` or `role`, `media_type`,
  `content_hash`, `byte_size`, `image_width`, `image_height`, and `supports`.

Follow-up task specs accept:

- `iri` or `task_iri`, otherwise DoxaBase uses
  `{packet_iri}/followup-task/{index}`;
- `task_text` or `text`;
- optional `label`, `priority`, and `targets`.

Query recipe specs accept:

- `iri` or `query_recipe_iri`, otherwise DoxaBase uses
  `{packet_iri}/query-recipe/{index}`;
- `query_text`;
- optional `label` or `query_recipe_label`, `description` or
  `query_recipe_description`, `query_language`, `query_engine`, and `targets`.

Use `analysis_views=[...]` for reviewed structured view specs. Use
`analysis_view_iris=[...]` only for views already present in the capsule or
created by the same packet call. Inside `analysis_views`, the `caveats` field
uses the normal analysis-view helper contract: pass existing caveat IRIs or
CURIEs, not inline prose. Put packet-level caveat text in the packet summary,
view descriptions, follow-up tasks, or an optional packet-supported pattern
unless the caveat has already been recorded as `rc:KnownCaveat`.

## Choosing The Helper

Use `record_analysis_packet` for analysis handoffs that need one durable
inspection seed across named subcorpora, reviewed view definitions, reusable
query cookbook entries, aggregate artifacts, visual outputs, and next tasks.

Use `record_profile_to_capsule_manifest` instead when the input is a reviewed
table/profile ingestion sidecar. Use `record_map_analysis_view_bundle` when the
only durable output is a set of logical views. Use packet `query_recipes` for
starter SQL or setup snippets that are not denominators. Use
`record_query_result` for a single executed query attempt or failure.

After recording a packet, follow the returned
`describe_context_slice(seed_iris=[packet_iri], profile="resource_brief")`
action to review the packet, linked views, artifacts, tasks, and optional
query recipes, pattern, and other bounded handoff context. The packet slice
also suggests `describe_analysis_view` for linked logical views so agents can
inspect denominators, source datasets, caveats, and query snippets from the
slice without hunting through generic outgoing references.
