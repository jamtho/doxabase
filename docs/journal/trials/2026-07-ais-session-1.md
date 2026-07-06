# AIS Real-Work Study — Session 1 (2026-07-06)

First real-work field session per doc 10 §2: a strong (Fable) analyst,
empty capsule, the real `ais-noaa` MinIO bucket (2 years, USA, 14.6M
MMSI/day index rows), low-resolution brief (two tracks, no tradecraft
taught). Study dir: `/home/codex/ais-study/` (brief, journal, bridge log,
expert questions, capsule). Audit report copy:
`/home/codex/doxabase-reports/ais-session1-report.html`.

## Outcome

Capsule validates (scope=all). 2 real datasets + 5 analysis views mapped,
20 observations, 13 claims, 8 patterns, 20 evidence, 14 caveats,
5 executable query snippets. Three vessel stories (a USN patrol boat; a
shared-MMSI chimera mixing a Shell platform with two Florida vessels; a
passenger ship rename with lay-up dating). Five methods recorded as
pattern + caveats + executable view + evidenced example: identity-change
classification with independent corroborators, multi-emitter detection,
silence-gap segmentation, draft-delta cargo events with terminal
inference, co-movement pair detection with a mobility statistic.

## Tradecraft scorecard (vs James's private examples)

- Co-presence → commercial-relationship: **rediscovered** (M5), refined
  with the mobility statistic; Weeks Marine dredge pair exemplar.
- Low-SOG dwell segmentation (static-in-port / special manoeuvres while
  transmitting): **not rediscovered** — M3 covers lay-ups via silence and
  M4 via draft, but nobody segmented active low-speed transmissions. A
  genuine gap for the expert channel / session-2 transfer to probe.
- Beyond the examples: M1/M2/M4 are new-to-brief; M4 (draft → cargo
  events → terminal identification without a port database) reads like
  real tradecraft.

## Pipeline claims for fast grading (about James's own fetch/index code)

1. `caveat/timestamp-cet-parse-bug`: parsed `timestamp` is UTC mis-parsed
   as CET/CEST (−1h/−2h flipping at EU DST dates); `base_date_time` is
   trustworthy.
2. `caveat/identity-year-constant`: static identity frozen per year;
   2,736/2,738 name transitions land exactly on Jan 1 (annual
   canonicalization suspected in the index builder).
3. `caveat/placeholder-encoding-shift-2025`: 2024 placeholder encodings
   (IMO0000000, zero dims) become NULLs in 2025.
4. `caveat/missing-day-2024-08-26`.

## Product friction

Two doc/tool mismatches (caveat evidence params; claim identity IRIs)
fixed same-day (`6e5e227`). Deferred to the distiller pass: vocabulary
discoverability (list_entities does not reach base_ontology; no
PhysicalType listing anywhere), `analysis_view_bundle` naming, pytz in
study venvs. Targeted errors again rated the redeeming feature.

## Next

James: grade via the report + alternative tools; answer the three
expert questions in `expert-questions.md`. Then session 2: cold, weaker
model, forensics questions only — the methods-transfer test.
