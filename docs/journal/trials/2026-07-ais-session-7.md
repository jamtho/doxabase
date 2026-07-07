# AIS Real-Work Study — Session 7: Track Context, Fast (2026-07-07/08)

Cold Sonnet analyst; the first session commissioned directly from expert
round 2 (James's VOCAB-NOTE review): prototype SQL views that make
positional track analysis fast, prove them, and record what earns its
keep. Brief: `/home/codex/ais-study/BRIEF-7.md`. Graph conforms;
patterns 34→36, observations 81→83, evidence 89→94; no queue debt.

## Verdict: two methods proven and recorded, and the expert's layering
## confirmed with numbers

- **M7 track-state classifier** (pattern `208f3abb…`): per-day
  underway/berthed/anchored/transition_day/stationary_unclassified from
  kinematics first, status codes second, plus a dwell-span layer
  (gaps-and-islands, corrected for the 2024-08-26 missing day; interior
  days only for dispersion). Proven by reproducing M6's recorded
  PENNSYLVANIA May-2024 itinerary — including correctly NOT calling two
  river slowdowns port calls — and it found a likely unrecorded 7th
  short Tampa call (recorded as observation, not story correction).
  `transition_day` as a first-class bucket is the method's own insight:
  the daily index's status_codes is a whole-day distinct list, so
  arrival/departure days carry both codes and naive classification
  over-labels transit as "berthed" (its first attempt did exactly that;
  it caught itself against known ground).
- **M8 draft-change contextualizer** (pattern `c768eaa1…`): joins M4
  draft events to M7 dwell spans (±1 day), labelling
  at_berth/at_anchor/no_dwell_nearby/dwell_unclassified. Event totals
  reproduced M4's recorded counts exactly.
- **The headline number**: dwell-attachment share orders seven vessels
  monotonically with independently-known cargo-story cleanliness —
  PENNSYLVANIA (genuine calls) 92–95% down to SULPHUR ENTERPRISE
  (the expert's own ballast-ambiguity exemplar) 38–53% — obtained with
  zero external trade knowledge. And the negative result is the
  valuable one: track context tells you WHERE a draft change happened,
  not WHY — SULPHUR ENTERPRISE's ballast intake and genuine loading
  both occur at berth. That is a quantitative confirmation of the
  expert's layer-1-fact / layer-2-interpretation design guidance.
- New caveat recorded: `m4-single-message-draft-glitch` — one stray
  message can be promoted into a fake draft event by the
  day's-first-value convention (broadcast-level spot check).
- Vocabulary alignment: dwell-span labels deliberately reuse
  aisv:dwellKind values rather than minting parallel terms; both methods
  stayed at Pattern level following M6's recorded precedent.

## Product findings

1. **Third sighting of MCP unknown-argument swallowing**, now with a
   measured cost: `get_doc` called with `id` instead of `doc_id`
   silently returned the doc INDEX instead of erroring — two wasted
   calls before the agent noticed. (Sightings 1–2: curator's source_*
   args dropped, wave 29.) The distiller-batch-2 ledger item now has
   trial-cost evidence from both sides of the study.
2. Minor discoverability friction: patterns live in graph "patterns"
   not "map" (one wasted list_entities), and the type-filter param name
   was guessed as rdf_type once.
3. Query economics: ~20 data queries total, 4 broadcast-level, none
   unfiltered — the index-first discipline from recorded cost guidance
   held.
