# Polymath Benchmark — run ledger (coordinator-maintained)

- 2026-08-13: seal written and hashed (see protocol §7) by the sealer
  session; coordinator has NOT read the seal and will not; judge-only
  materials (seal + extracted seal-side source texts + sealer's source
  ledger) at /home/codex/polymath-seal/ outside all repos.
- Ingester model, recorded BEFORE first launch per protocol §3:
  claude-sonnet-5 (Sonnet-class), same model for every session.
- Session chunking, decided before first launch (D2 governs changes):
  s1: allowlist 1-3 (context posts); s2: 4; s3: 5-6; s4: 7-8;
  s5: 9-10; s6: 11-13; s7: 14-15; s8: 16-18; then one synthesis
  session; then export + freeze.
- Full variant (not CORE) selected at launch.
- Ingester working directory /home/codex/polymath-study/ (neutral
  name; the ingester is not told a benchmark exists).
- 2026-08-13: s1 complete — allowlist 1-3, all fetches direct (no
  substitutions), 39 observations / 2 typed episodes, conforms, zero
  staged debt; coverage: post-1 comments 1-85 recorded, 86-247
  verified pingbacks/off-topic (logged); posts 2-3 covered. Ingester
  parsed HTML locally rather than via summarizing fetch — anchors
  verbatim-verifiable.
- 2026-08-13: s2 complete — allowlist 4 (the first mathematical
  thread), direct fetch, 53 new observations / 3 typed episodes
  (capsule now 92 obs / 5 episodes), conforms, zero staged debt; all
  181 non-pingback comments covered, remainder verified pingbacks.
  Notable for the record: the ingester exercised triple-retraction
  for the first time in this capsule (schema probes cleanly
  retracted) — the discipline holding without prompting.
- 2026-08-13: s3 complete — allowlist 5-6 (the bounds branch + the
  triangle-removal thread), 48 new observations / 3 typed episodes
  (capsule 140 obs / 8 episodes), conforms, zero staged debt; full
  comment coverage on both threads. Operational note: Tao's blog
  paginates at 50/page (Gowers's does not) — caught by the ingester
  cross-checking extracted counts against page headers; a silent
  half-thread loss was avoided by mechanical verification, not luck.
- 2026-08-13: s4 complete — allowlist 7-8 (quasirandomness thread +
  reading seminar), 43 new observations / 4 typed episodes (capsule
  183 obs / 12 episodes), conforms, zero staged debt; thread-7
  coverage records three documented low-content folds; the ingester
  verified Tao's thread was genuinely single-page (sidebar-widget
  false pagination signal checked mechanically before trusting).
- 2026-08-13: s5 complete — allowlist 9-10 (strategy consolidation +
  numbers branch), 55 new observations / 4 typed episodes (capsule
  238 obs / 16 episodes), conforms, zero staged debt; full coverage
  both threads with six named side-strand gaps recorded; thread-10
  pagination ran to three pages, caught via the link chain rather
  than string matching. Anchor note for the judge: five inline
  numbering collisions found on thread 9 — WordPress comment IDs were
  the reliable anchor, as the ingester's records reflect.
- 2026-08-13: s6 complete — allowlist 11-13 (governance micro-thread,
  mid-project self-review, the main-push resumption), 60 new
  observations / 3 typed episodes (capsule 298 obs / 19 episodes),
  conforms, zero staged debt; ALL 235 comments covered (zero
  pingbacks existed); four named gaps. Dialect discipline note: the
  ingester checked EpisodeShape corpus-scoping text before reuse and
  correctly declined to force kernel/email dialect shapes onto
  mathematical material.
- 2026-08-13: s7 complete — allowlist 14-15 (the endgame: the numbers
  branch's close + "problem solved (probably)"), 40 new observations
  / 3 typed episodes (capsule 338 obs / 22 episodes), conforms, zero
  staged debt; full coverage; one D3-class note: source 14's URL 301s
  to a longer canonical slug, followed transparently (same page, not
  a substitution). Session 5's c'_5 gap resolved by this session's
  material; session 6's quasirandomness-definition gap explicitly
  rechecked and confirmed still absent.
- 2026-08-13: s8 complete — allowlist 16-18 (the generalization push
  and the branches' ends), 47 new observations / 3 typed episodes,
  conforms, zero staged debt. HARVEST CAMPAIGN COMPLETE: 8/8
  sessions, all 18 allowlist sources read in full (Jan 27 - Jun 25
  2009, research comments ~1-1270), capsule at 385 observations /
  192 claims / 25 typed episodes / zero staged debt throughout.
  Longitudinal gap discipline held: two cross-session gaps re-checked
  to the end (one resolved s7, one confirmed absent to the last).
  Next: the synthesis session (arcs), then export + freeze, then the
  judge.
- 2026-08-13: SYNTHESIS complete — 9 kh:Arc recorded (all with pivot
  quotes, terminus basis+surface; one mixed terminus recorded
  honestly), 4 near-miss arcs REFUSED with reasons, 3 abandoned
  approaches retained as DeclinedOptions (one with a revival
  condition), two literal shared members braiding three arcs;
  conforms, zero staged debt; 394 obs / 9 patterns / 26 episodes.
- 2026-08-13: OUTPUT FROZEN — capsule + journal copied to
  /home/codex/polymath-frozen/, SHA-256 hashes in FREEZE-HASHES.txt
  there. The judge launches next; per protocol §3 it is the FIRST
  and only reader of the seal, must verify the seal hash before
  opening, and grades in registry order (seal hash first hex digit
  is even).
- 2026-08-13: VERDICT — **PASS** (not STRONG PASS; the ≥3-RECOVERED
  gate missed by one, with the judge explicitly rejecting the laxer
  reading that would have granted it). 6/6 HIGH arcs ≥ PARTIAL, 2
  RECOVERED, 5/5 negatives correct, ZERO hallucinated established
  claims across 394 observations, headline 4.5 vs the 3.0 bar;
  anchor audit 81/81 comment-level checks passed on the live 2009
  pages. Four plausible-novel governance arcs found that the seal
  never anticipated — the retrospectives-are-winner's-history thesis
  demonstrated against the trial's own seal. The sealed prediction
  (terminus surfaces) NOT borne out — recorded as a clean
  couldn't-say: v3 scopes narratedTerminus to bot-notices, making
  the predicted split inexpressible. No D1 deviations; run valid;
  the seal is spent and now published in polymath-judge/ for
  hash-verification against the protocol's pre-commitment.
