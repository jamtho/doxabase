# Design Doc 13: The Capsule Workbench

**Date**: 2026-07-12 (handover design — James asked for a doc he can
"later run with")
**Status**: Design for future implementation sessions. Companion to
doc 11: the observatory is the *curated, public* rendering of a
capsule; the workbench is the *exploratory, analyst-facing* one. They
share their lower layers by construction, in one repo with two build
targets.
**Status update (2026-07-20)**: implementation lives in-repo as the
`workbench/` package as of this date, at the owner's direction
("humans can't really interface with the capsules without it") —
superseding the separate-repo phase it briefly went through
(`jamtho/doxabase-workbench`) and returning to §3 decision 2's original
"one repo" call.
**The ask**: one web system that connects to a capsule (+ the S3
frames it describes) and exposes the contents for exploratory work,
with the bulk shared across domains and project-specific customization
on top — because "small details can often be 50% of the value of a
human-facing system," the customization layer is a first-class design
concern, not an afterthought.

---

## 1. What it is

A local-first web application an analyst points at a capsule:

```
doxabase-workbench capsule.sqlite   →   http://localhost:PORT
```

No hosting, no accounts, no infrastructure — the same deployment
weight as `doxabase-report`, which it subsumes as its static sibling.
It reads the capsule via the installed wheel (Python API, read-only)
and the frames via DuckDB. Nothing in the serving path writes to the
capsule in v1: **agents write, humans see** — the workbench is where
the expert reads, checks, and decides what to tell their agent next.
(The expert-channel loop this study ran through chat + KML files +
HTML reports is the workbench's exact use case, done by hand 14
times.)

## 2. Layer architecture (the shared/custom split James asked about)

- **L1 — capsule access** (shared, thin): a local JSON facade over the
  existing core read calls (project_brief, describe_resource,
  describe_dataset, search, list_entities, list_revisions,
  validate_graph) plus a frame-query endpoint (DuckDB over described
  datasets, read-only, row-capped). Deliberately NOT the MCP surface —
  that is agent-optimized (char budgets, envelopes); this is
  UI-optimized (pagination, prefetch). Same core underneath, so the
  distillation ceilings are untouched.
- **L2 — generic explorer** (shared, the bulk):
  1. **Resource pages**: any IRI rendered — types, literals, links
     followable in both directions, claim chains expanded inline,
     history sidebar (what revisions touched this).
  2. **Search + orientation**: the project brief as landing page;
     search-as-you-type; the caveat catalog as a first-class view
     (analysts should trip over caveats, by design).
  3. **The frame browser** — the killer feature: pick a described
     dataset → its schema WITH column semantics and caveats alongside
     → query it (SQL box + saved recorded views one click away) →
     results grid with export. Data never appears without its
     semantics; this is what no warehouse UI does.
  4. **Map panel**: doc 11's exporter core in live mode — geo-typed
     resources and frame layers on MapLibre, with the round-6
     affordances (export-view-as-KML/KMZ, folders by classification).
  5. **Method pages**: a recorded method rendered as contract
     (doc 12): invariants, evidenced parameters (plots inline — the
     session-12 threshold plots ARE the parameter's trust surface),
     realizations, dependency graph, failure modes.
  6. **Queue views**: staged revisions with previews; the review
     decision itself stays with agents/CLI in v1 (read-only rule),
     but SEEING the queue is orientation.
- **L3 — domain configuration** (per project, where the 50% lives):
  entity-page templates ("vessel page": identity slots, stories,
  stops, transits, map inset; other domains define theirs), layer
  definitions and styling, saved views, landing-page arrangement,
  vocabulary-aware labels. Configs live with each study, not in the
  workbench repo. The template language should be boring (declarative
  JSON/YAML + component slots), because domain configs will be written
  by agents.

The observatory (doc 11) = a build that snapshots L2 views through the
export-eligibility gate into static artifacts. One codebase, two
targets: `workbench` (live, local, everything) and `observatory`
(static, reviewed, public). The shareability machinery
(export_preflight + human review) sits exactly at the boundary.

## 3. Decisions taken (overridable)

1. **Local-first, read-only v1.** Writes via the workbench (even
   annotations) wait until the ephemeral-entities and review-lane
   designs settle; a premature annotation feature would create a
   second write path around the epistemic ladder.
2. **One repo** (`doxabase-observatory` per doc 11 — the workbench is
   its superset; rename the repo if that reads better), consuming the
   wheel; no doxabase-core surface growth.
3. **DuckDB-Wasm only in the observatory target** (static); the
   workbench uses server-side DuckDB (it's localhost — simpler, and
   big frames stay off the browser heap).
4. **v1 MVP against the AIS capsule**: landing brief + resource pages
   + search + caveat catalog + frame browser over stops_series/
   m11_survey + map panel with the two existing KML demos re-rendered
   as layers. That list is deliberately the study's own daily needs.

## 4. Open questions for implementing sessions

1. Auth story when someone inevitably exposes it beyond localhost
   (answer should be "don't — use the observatory target," but say so
   loudly in the UI).
2. How method pages render two realizations side by side (doc 12's
   comparison affordance).
3. Whether resource pages get a "explain this to me" agent hook later
   — out of scope for v1, noted because someone will ask.
4. Performance floor: resource pages must render in <100ms against
   the AIS capsule (2.5MB, ~4k resources) without indexes; if a
   bigger capsule breaks that, the fix is capsule-side (the corporate
   backend), not workbench caching.

## 5. First implementation cut (for whoever runs with this)

Read doc 11, this doc, and the round-4/6 expert observations in the
AIS capsule (the map directives). Build L1 as ~200 lines of FastAPI
over the wheel + one DuckDB endpoint; build resource pages + search
first (they exercise L1 completely); then the frame browser; then the
map panel by porting story_kml.py's queries to GeoJSON. Ship each
step against the real AIS capsule; the study's expert (James) is the
design authority on what feels right — his round-6 rule applies to
every screen: lead with what you're trying to show.
