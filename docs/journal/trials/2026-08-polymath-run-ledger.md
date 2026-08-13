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
