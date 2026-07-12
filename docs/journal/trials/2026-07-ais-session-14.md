# AIS Real-Work Study — Session 14: The M12 Contract (2026-07-12)

Fable contract author; phase 1 of the doc-12 RDF-method-contracts
pilot. Brief: `/home/codex/ais-study/BRIEF-14.md`. Graph conforms, no
staged debt; mc: vocabulary (20 terms) + M12 full contract (+140
triples) + M11 sketch applied via staged revisions; blind bundle
exported (333 triples, parse-verified, SQL-clean, M11-free) for the
phase-2 cold regeneration now running.

## What phase 1 established

- **The mc: vocabulary held at 20 terms**, every one ≥2-method
  justified from how M12/M11/M9 are actually written: MethodContract,
  Parameter, Invariant, Realization; consumesDataset/Column,
  dependsOnMethod, outputGrain/outputMeaning, hasParameter/Invariant/
  Realization/FailureMode (failure modes reuse rc:KnownCaveat — no new
  machinery), value/unit/parameterRole, statement/constrainedBy,
  engine. rc:citesClaim (landed this morning) is doing the evidence
  wiring — its first production use.
- **M12's contract is complete**: 5 property-style invariants —
  including silence-terminates, which structurally encodes the
  session-13 defect (a regenerated realization that fails it has
  reproduced the bug); 7 parameters with real evidence citations
  (0.5kn/600s cite session-13's claim; 1800s carries the 70-day
  phantom-stop story; 120s honestly labelled "design choice, no
  survey"; the glitch-screen trio cites session-12) — all carrying
  assessedAt/assessmentDataWindow, so they age visibly.
- **Doc-12 decision points, answered with evidence**: (1) property-
  style invariants confirmed — and the promotion criterion already has
  its first instance (silence-terminates exists because a real
  regression happened); (2) parameters free-standing + method-scoped,
  with the refinement that shared EVIDENCE is cited while parameter
  RESOURCES stay duplicated (re-tuning independence); (3) realizations
  as own resources confirmed — v1-vs-v2 identity (same contract,
  different behaviour) was immediately representable; (4) regeneration
  authority: staged-behind-invariant-report, strengthened — the
  original author with full context shipped a realization violating
  its own then-unstated invariant.

## The couldn't-say list (the design session's key input)

1. Threshold BANDS (two-sided bounds with a mandated ambiguous middle)
   — value+unit+role forces one primary value.
2. Sequenced decision procedures (M11's crowd→geometry→heading-
   corroborates-never-overrides ordering) — prose only; methods that
   are procedures over signals strain L1.
3. Derived-metric definitions (hollow_frac etc.) — deliberately left
   as prose to avoid the relational-algebra slide; regenerators must
   infer from words.
4. Parameter INTERACTIONS (the 0.5kn/120s under-merge trade-off is a
   property of the pair).
5. Failure modes not yet promoted to caveats are unreachable by
   hasFailureMode (M12's dredge-under-merge and swing-fragmentation
   live only in pattern prose — promotion wanted).
6. Run-scope inputs (the sample list is neither dataset nor
   parameter) — relates to derivedFromRun.
7. Invariant checkability GRADE (output-only vs needs-constituents) —
   matters for generated tests.

## Friction

Prose-echo policy needs stating (phase-1 authors read the original by
design; the ban is on pattern text/SQL — define "not the pattern text"
at phrase granularity). Search is literal-only (IRI local names
unfindable); describe_resource incoming links on patterns returned
nothing; list_entities needs exact full IRIs; stage_revision reports
history-side triple counts (momentarily alarming). All → batch-2/3
ledger.

## Phase 2 (same day): the blind regeneration — PASS

A cold agent with ONLY the 333-triple bundle + data access rebuilt
M12: **426,207 events vs the original 427,134 (−0.22%)**; flag rate
6.92% vs 7.0%; the post-fix maximum event reproduced to the decimal
(89.709 days vs the contract's quoted "plausible 89.7"). All five
invariants PASS — and the invariant machinery earned its keep inside
the pilot itself: the regenerated SQL was initially non-deterministic
(same-second broadcast collisions left window-function ties arbitrary;
five runs, five counts) and flicker-containment caught it; fixed to
bit-identical reruns with integer run-ids and single-threaded
canonical execution.

The ambiguity list independently confirms phase 1's couldn't-say items
(hollow_fraction named-but-undefined = the largest interpretive gap)
and adds three the contract vocabulary must express: ordering
determinism under timestamp ties; duplicate-broadcast handling
(120,633 exact dupes, unaddressed); run-scope inputs (already on the
list). And the star finding: the blind agent discovered the
**base_date_time separator shift at the 2024/2025 boundary** — a real
ingest inconsistency five sighted sessions silently absorbed via CAST
— now a recorded caveat (curator-verified live) and a pipeline
reminder for James. Fresh eyes constrained to a spec see what
familiarity glosses.

Verdict for doc 12: behavioural regeneration from RDF contracts works
at the 99.8% level, the residual is attributable to exactly the gaps
phase 1 predicted plus determinism/dedup, and "regenerated code stages
behind an invariant report" moved from lean to law — the report caught
a real bug in the pilot's own regenerated code.
