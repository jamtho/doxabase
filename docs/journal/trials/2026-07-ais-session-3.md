# AIS Real-Work Study — Session 3: Literature Onboarding (2026-07-06)

Cold Sonnet analyst; capsule-first orientation, then the provider's
documentation (MarineCadastre PDFs via the ArcGIS Sharing REST API — the
hub page itself is an empty JS shell) and the receiver-map gpkg.
Rule enforced: docs are provider claims with provenance; where docs
contradict capsule evidence, evidence decides. Study dir artifacts:
external/ (5 PDFs + gpkg), JOURNAL-3.md. Graph conforms after +10
observations, +10 claims, +6 patterns, +3 caveats, +16 evidence.

## Headlines

1. **Probable mechanism for the identity freeze found in the docs**:
   the provider runs an MMSI-keyed identity-correction database
   (AVIS 2015-23, AVID 2024+) with fuzzy-logic correction of static
   fields. Recorded as a REFINEMENT, not confirmation — correction
   cadence/boundary alignment is undocumented — but it coherently
   explains both the near-annual freeze and the navy boat's surviving
   mid-year toggle (corrections keyed per release, genuine transponder
   changes occasionally passing through).
2. **A new asymmetric encoding shift found by cross-checking a doc
   column against live data**: heading/cog sentinels (511/360) become
   NULLs at the 2025 boundary while sog's 102.3 sentinel survives in
   both years — stated in no document; new severe caveat
   `sentinel-encoding-shift-2025`.
3. **The expert's remembered 40-50 nm coverage rule: verified almost
   verbatim in the FAQ** — memory graded against literature, a nice
   inversion.
4. **M3 coverage-blindness demonstrated in both directions** with the
   290-station gpkg joined against M3's own output: coastline-hugging
   gaps over-called (endpoints 19-22 nm from stations), far-offshore
   short gaps under-called (endpoints 270-360 nm out). Recorded as
   caveat + evidence; SQL upgrade deferred as flagged future work.
5. Provider-internal inconsistency flagged, not resolved: FAQ says ~200
   stations; the ArcGIS item text and the gpkg say 280-290.
6. Placeholder-encoding shift and sentinel tables CONFIRMED by the data
   dictionary; base_date_time confirmed UTC (docs silent on the CET bug,
   consistent with it being project-side); message-type merging
   formalized from expert aside into documented caveat.

## Friction → actions

- The caveat-evidence rejection it hit was NOT a product bug: the study
  venv's wheel predated the wave-25 fix. Wheel refreshed; fix verified
  through the study bridge; plumbing-check caveat removed cleanly.
  **Lesson for the parting notes: refresh study venv wheels after
  product fixes — trial environments pin the wheel they were built
  with.** The stale map_authoring doc claim it inferred was actually
  correct-but-undeployed.
- Shell quoting for JSON-with-apostrophes bit a second agent (scratch-
  file workaround again) — promoted to a firm distiller item: bridge.py
  should accept a payload file (e.g. `call <tool> @args.json`).
