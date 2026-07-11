# Design Doc 11: The Capsule Observatory

**Date**: 2026-07-12 (Fable, final day)
**Status**: Design for handover — implementation belongs to future
sessions in a SEPARATE repository. This doc is the contract.
**Origin**: The AIS field study's expert channel converged on "maps are
the interface" (round 4, recorded in the study capsule), and the study
needs a public face that doubles as DoxaBase's demonstration. This doc
designs that face generically: a web/map application that renders ANY
capsule (plus the S3 frames it describes), with the AIS study as the
first target.

---

## 1. What it is

A read-only rendering stack over two inputs:

1. **A capsule** (or its TriG export): the semantic layer — stories,
   events, places, methods, caveats, claims, provenance.
2. **The frames the capsule describes** (parquet in object storage):
   the population layer — censuses, stop series, survey caches.

Output: a map-first web application where every rendered feature
traces, on click, to its claim chain — summary, evidence, method IRIs,
confidence, caveats in scope. The natural-language parts of the graph
render as notes attached to features; RDF structure is the primary
input (the AIS aisv: vocabulary already satisfies this; that was the
point of session 10).

Two build targets from the same exporter:

- **Expert mode** (back office): all layers, all caveats, dense; the
  KML path (already prototyped: `docs/journal/ais-study/story_kml.py`)
  is a peer output of the same exporter core for Google-Earth-style
  gut-reading.
- **Public mode**: promoted/reviewed resources only, controlled
  wording by claim type and confidence, and the anti-insinuation rule
  as a rendering constraint: a line between two features always states
  its relationship type; proximity is never drawn as implication.

## 2. Architecture: static-first, agent-free serving path

```
capsule.sqlite ──► exporter (new, runs offline) ──► artifact bundle:
  - layers/*.geojson or *.pmtiles   (feature layers, per theme)
  - frames/*.parquet                (population layers, pass-through)
  - provenance/*.json               (claim chains keyed by feature id)
  - report/*.html                   (existing doxabase-report output)
  - manifest.json                   (layer registry, mode, data window)
        │
        ▼
object storage (S3/R2) ──► static web app (MapLibre GL
  + DuckDB-Wasm for in-browser queries over frames/*.parquet
  + deep links from map features into report/*.html anchors)
```

Principles:

- **No live agent, no live capsule in the serving path.** The web app
  serves reviewed exports. Analysis happens in sessions; publication
  is a deterministic build. (This mirrors the export-eligibility
  posture: scanner + human shareability review before any bundle goes
  public.)
- **The exporter is the only new software of substance.** The front
  end should start as a single static page + MapLibre + manifest
  loader; resist app-framework gravity until layers demand it.
- **Frames render as frames.** The shuttle census, the M11 survey, the
  stops series — heatmaps/point layers straight from parquet via
  DuckDB-Wasm, never re-encoded into the graph. The graph supplies
  the semantic overlays (stories, promoted exemplars, caveat regions).
- **Data windows on screen.** Every view states its
  assessedAt/assessmentDataWindow — the indexicality discipline
  surfaces in the UI, not just the graph.

## 3. Repository and boundary decisions

- **New repo** (suggest `doxabase-observatory`): the exporter + front
  end. It consumes capsules via the installed doxabase wheel and
  export bundles — NO new MCP tools, NO doxabase-core surface growth.
  This keeps the Distillation Program's ceilings untouched and lets a
  marketing-speed artifact iterate without touching the product's
  conceptual budget.
- Domain configs (which layers, which modes, styling) live with each
  study, not in the observatory repo. The AIS config is the reference
  implementation; other domains supply their own.
- If the observatory's needs expose genuinely generic capsule gaps
  (e.g. "there is no cheap way to enumerate all geo-typed resources
  with their claim chains"), those flow to the distiller ledger like
  any other case-study finding.

## 4. MVP cut (the AIS demonstration)

Layer 1 — **story map**: the promoted vessel stories as features
(dwell poles, identity-change sites, event locations), each opening
its claim chain + a link into the session report. This is the KML demo
generalized.
Layer 2 — **the shuttle census** (frame): 820 shuttles as
routes/poles, class-filtered, with the 17-stopped population
highlighted and their stop-kind classifications shown.
Layer 3 — **M11 stop classification** (frame + method overlay):
berth/anchor/ambiguous points with the threshold provenance one click
away (the session-12 plots ARE the trust surface — embed them).
Deliberately absent from MVP: search, arbitrary query UI, any
natural-language interface. Add only against observed need.

## 5. What this is not

- Not a dashboard product; layers exist because a story or method
  earned them.
- Not a live analytical service; if a public user needs fresh
  analysis, that is a session, with review, then a rebuild.
- Not a second place where knowledge lives. The capsule remains the
  single source; the observatory is a projection. If the projection
  needs something the graph can't say, the graph grows (via the
  normal evidence discipline) — the projection never invents.

## 6. Open questions for the implementing sessions

1. PMTiles vs plain GeoJSON at AIS scale (820 shuttles: GeoJSON is
   fine; 7.3M stationary windows: tiles or DuckDB-Wasm-side
   aggregation — measure first).
2. Track rendering: fix-clouds (honest, heavy) vs simplified lines
   (light, lossy) — probably zoom-dependent, expert mode defaulting
   honest.
3. Provenance packet size: what is the smallest claim-chain JSON that
   remains genuinely useful? (Shared question with other case
   studies; answer empirically.)
4. Whether doxabase-report and the observatory converge on one
   exporter core (likely yes eventually; do not force it in MVP).

## 7. Handover expectations

Implementing sessions should read, in order: this doc; the round-4
expert observations in the AIS capsule (the map-interface directive
and the squiggle-reading rationale); `story_kml.py` (the cheapness
bar); session 10's trial record (why stories-as-RDF is load-bearing);
the export_preflight/shareability flow (public mode must run it).
First deliverable: the exporter producing layers 1–2 from the real
AIS capsule, viewed locally in MapLibre, before ANY hosting decisions.
