# JOURNAL-3: Literature Onboarding Session

## Orientation

Read BRIEF-3.md only (per instructions, did not read prior JOURNAL*.md,
BRIEF.md/BRIEF-2.md, tools*.json, expert-questions.md, or /workspaces/doxybase).
Ran `bridge.py tools` once into `tools3.json`. Oriented via
`project_brief`, `graph_overview`, `get_doc(start_here)`, `describe_dataset`
on both `broadcasts` and `daily-index`, and `describe_resource` on the M3
(`silence-gap-events`) analysis view, plus `search` for "coverage",
"receiver", "message type" before touching the internet at all, as the hard
rules required.

Capsule state at start: 7 datasets/tables, 49 columns, 31 observations,
18 claims, 11 patterns, 21 `rc:KnownCaveat` entities (8 attached to
broadcasts/daily-index, 3 each for M1/M2/M3-ish method caveats, 2 for M4/M5).
5 analysis views (M1-M5), one expert observation already flagged the
40-50 nm coverage rule as "VERIFY against documentation before trusting."

## Documentation ingest

`hub.marinecadastre.gov/pages/vesseltraffic` is an ArcGIS Hub / Ember SPA --
the raw HTML has no content, it's all client-rendered. Worked around this by
hitting the ArcGIS Sharing API directly (`arcgis.com` domain, in bounds):
searched `title:"Vessel Traffic" type:"Hub Page"` to find the page's item id
(`22fb5273ccb54f6aa423f6667a856761`), then fetched
`/sharing/rest/content/items/{id}/data` to get the page's JSON layout
(markdown cards + hrefs) without needing a JS renderer. Same technique for
the "AIS Base Stations" ArcGIS item (`8383640cd72e463caa77d230978c24bd`):
its item JSON gave both a text description (station counts) and the direct
`marinecadastre.gov` zip URL, which is a "direct file URL linked from
arcgis.com" per the hard rules.

Downloaded into `external/`: `faq.pdf`, `data-dictionary.pdf`,
`VesselTypeCodes2018.pdf`, `point-data-summary.pdf`, `Other_AIS_Resources.pdf`
(all from `coast.noaa.gov`, directly linked off the hub page), plus
`AISBaseStation.zip` -> `AISBaseStation.gpkg` (from `marinecadastre.gov`,
linked off the arcgis.com item). Did not fetch the linked GitHub repo
(`ocm-marinecadastre/ais-vessel-traffic`) -- it's outside both allowed
domains and is a code repo, not a "direct file URL for this AIS product", so
treated it as out of scope even though it's linked from the hub page.

`pypdf` text extraction worked cleanly on all 5 PDFs. `duckdb` `spatial`
extension read the gpkg with no issues (`ST_Read`, `ST_Centroid`, `ST_X/Y`).

## Reconciliation approach

Recorded 9 `record_observation(kind="claim")` entries, each citing a specific
PDF (or the gpkg/item) with page/section provenance via
`source_path`/`source_section`/`source_kind="rc:DocumentationSource"` (or
`rc:QuerySource` for two claims that are actually this session's own
empirical checks against the live parquet + the receiver gpkg, not provider
prose). Then 6 `record_pattern` entries, one per reconciliation category,
each giving an explicit confirmed/contradicted/silent/refined verdict with
`pattern_targets` pointing at the relevant caveat(s) and `supporting_claims`
at the claim IRIs. Minted 3 new `rc:KnownCaveat` map facts
(`message-type-merging`, `sentinel-encoding-shift-2025`,
`m3-coverage-geometry-blind`) via `record_map_fact` for findings that
deserved to be first-class map facts, not just observations -- these are
additions, not edits to existing caveat text, so `record_map_fact` (direct
write) was appropriate rather than `stage_revision`; nothing was overwritten.

Chose NOT to use `record_claim_reconsideration` anywhere: none of the five
named caveats had a distinct prior `rc:Claim` resource to reconsider (the
"upstream mechanism unconfirmed" language lives in the caveat's own
description, not a separate claim), and none of the doc findings actually
contradicted an existing empirical claim -- they confirmed, refined, or
stayed silent. Reconsideration would have been the wrong tool here per its
own doc ("a later claim changes how an earlier claim should be read");
nothing here changed a prior reading, so plain corroborating/refining claims
were the right weight.

## Friction

- `record_map_fact(kind="caveat")` rejects `evidence_summary`/
  `evidence_sources` in spec with "unknown spec field(s)", even though the
  `map_authoring` doc explicitly says caveat facts "accept `evidence_summary`
  + `evidence_sources` (and optional `evidence_iri`) in spec, writing a
  linked `rc:Evidence` resource." The `mcp_tools` generated reference agrees
  with the *rejection* (lists only `iri`/`description`/`label`/`impact`/
  `severity`/`targets` for this kind) -- so `map_authoring` (hand-written) and
  `mcp_tools` (generated) disagree with each other, and the generated one
  matches actual behavior. Worked around by not passing those fields on the
  caveat writes and instead relying on the claims/patterns that target the
  same caveat IRIs (which do carry full evidence) for the evidence trail --
  `describe_resource` on a caveat should still surface "what backs this" one
  hop away via incoming claim/pattern targets, just not via a direct
  caveat->evidence edge.
- Shell quoting: JSON payloads with apostrophes (e.g. "capsule's") break
  single-quoted `bash -c` invocations of `bridge.py call`. Worked around by
  writing each payload to a scratch JSON file and calling through a tiny
  Python subprocess wrapper (`bcall.py` in the scratchpad dir) instead of
  inlining JSON on the command line. Future sessions hitting the same wall
  should just do this from the start rather than fighting shell escaping.
- The hub.marinecadastre.gov page itself is unreadable without JS; the
  ArcGIS Sharing REST API (`/sharing/rest/content/items/{id}/data`,
  `/sharing/rest/search`) is the reliable way to get an ArcGIS Hub page's
  actual content and is squarely inside the `arcgis.com` allowance.

## Surprises

- The sharpest finding wasn't in any PDF: cross-checking the data
  dictionary's throwaway "Null Allowed" column against the live 2024 vs 2025
  broadcasts data showed `heading`/`cog` fully swap their "not available"
  encoding (511/360 -> NULL) at the 2024/2025 boundary while `sog`'s 102.3
  sentinel is untouched in both years -- an asymmetry no document states and
  the existing `ais-sentinel-values` caveat didn't distinguish.
- The M3 coverage-envelope check produced an unambiguous concrete
  counterexample in each direction on the first attempt: a Gulf-coast MMSI
  whose ~400 km "coverage exit" gaps have both endpoints 19-22 nm from a
  receiver (comfortably inside the 40-50 nm envelope), and a cluster of
  malformed-MMSI records whose <300 km "local gaps" sit 270-360 nm out in
  the open North Atlantic (already outside the envelope on both ends).
  Displacement alone really cannot stand in for coverage geometry.
- Two provider documents from the same family (the AIS FAQ vs. the "AIS Base
  Stations" ArcGIS item) give different receiver counts (~200 vs. 130+150).
  Recorded as a noted inconsistency rather than silently picking one.
