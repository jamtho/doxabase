# AIS Real-Work Study — Session 2: The Transfer Test (2026-07-06)

Cold Sonnet analyst, capsule-only inheritance (predecessor scratch files
forbidden), three forensics tasks with hidden probes. Study dir:
`/home/codex/ais-study/` (JOURNAL-2.md, bridge log). All three tasks
answered; graph validates clean after its recordings.

## Transfer verdict: the inheritance works

- **Retrieval over re-derivation, with citations**: used M1, M2, M4, M5
  and eight caveats BY IRI; re-ran M5's recorded query verbatim for the
  MAGDALEN task and reproduced the predecessor's numbers exactly —
  verified, not trusted. The CET-timestamp caveat was load-bearing in
  every timing claim (all times from base_date_time).
- **The untaught gap emerged.** James's low-SOG dwell tradecraft
  (deliberately never taught, not found by session 1's strong model)
  was DERIVED by the weaker model under port-call task pressure: its new
  M6 method screens the index for stationary clusters, then detects
  SOG<1kn threshold crossings at broadcast level, cross-checked against
  draft direction. Scaffolded by recorded M4 logic + caveats — the
  capsule didn't contain the method, but it contained enough for a
  modest model to build it.
- **The group improved its own memory.** Session 2 found a genuine gap
  in session 1's M1 (same-hull corroboration misses renames where IMO is
  never reported and the call sign also changes — 367615990 is the
  concrete counterexample) and recorded it as a caveat claim with a
  suggested fix. Weak model, strong model's method, evidence-backed
  correction: the epistemics working as designed.
- **"Nothing the previous analyst got wrong"** — every exercised method
  and caveat held under independent verification.

## Task answers (graded by James separately)

1. 367615990: same hull, JACOB BRENT→PERCIVAL, Galveston-based; rename
   real but date indeterminate (no lay-up window to pin it; the raw
   boundary flip at 47s across midnight correctly identified as the
   feed artifact). Flagged itself as an M1 corroboration failure case.
2. 369305000 MAGDALEN: one clear associate (RB WEEKS, 171 pair-days,
   mobility 622km, shared five-job dredging itinerary); ~19 co-locators
   correctly dismissed as jobsite noise; one 7-day case recorded as
   inconclusive rather than asserted.
3. 338617000 PENNSYLVANIA: six May-2024 terminal stays (Lake Charles ×2,
   Tampa ×2 with anchorage/berth split, Baton Rouge, Beaumont/Port
   Arthur) with arrival/departure timing and load/discharge direction
   from draft.

## Friction → actions

- The agent flagged two "prompt-injection attempts": these were the
  harness's own legitimate system notices (date-change reminder;
  file-modified note). Misdiagnosis, but the *posture* — distrust
  instruction-bearing tool output, refuse concealment, report — is
  exactly right and worth preserving in trial briefs.
- Fixed same-day: gen_docs now renders spec fields for the four
  flat+spec recorders (the agent couldn't discover `pattern_iri`, which
  existed but was undocumented); pytz added to the study venv.
- For the distiller: record_observation's kind=claim spec-nesting
  wording in the generated doc; JSON-with-apostrophes ergonomics for
  bridge payloads.
