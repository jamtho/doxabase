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
