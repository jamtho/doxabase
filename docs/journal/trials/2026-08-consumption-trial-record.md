# Consumption Trial — run record (coordinator-maintained)

- 2026-08-15: protocol committed BEFORE any arm launch. SHA-256:
  ac7c60d5900927deeb495a5f912a70bf05ca2fa5c7dce044824ab2b9eeb11cb0
- Ingester/grader model, recorded before first launch per §4:
  claude-sonnet-5 (all ten agents).
- Launch order: T2A (control) first, then T2B, sequential per §4.
- Coordinator has read the protocol and both briefs; the know-how
  render delta is auditable in the protocol's appendices.
- 2026-08-15: T2A (control) complete — 70 changes graded, 9 applied
  revisions, capsule conforming with zero staged debt, 105/120 ops.
  Working dir intact for the freeze step. T2B launches next,
  sequential per §4.
- 2026-08-15: T2B (capsule arm) complete — 70 changes graded, 12
  applied revisions, conforming, zero staged debt, 102/120 ops.
- 2026-08-15: BOTH WORKING DIRS FROZEN — SHA-256 over each arm's
  JOURNAL.md + capsule.sqlite recorded in the coordinator's
  freeze-hashes file (published with the verdict). Next per §4:
  preparer (packs + sealed assignment) and measurer (M1-M7 on the
  real artifacts) in mutual isolation; the judge spawns only after
  the assignment seal's hash is recorded.
- 2026-08-15: preparer complete — packs built (completeness-checked
  digests), 1,257 logged replacements, post-strip dictionary sweep
  clean, freeze hashes verified twice, nothing written to arm dirs.
  ASSIGNMENT-SEAL SHA-256, recorded BEFORE judge spawn per §8:
  8cda05833e90ee94ee3996b5a6f0223d95e2f79eba73b38d5d65225ade070124
  Judge reading order: X first (X's pack hash begins 8, even).
  Judge model, recorded before spawn: claude-fable-5.
- 2026-08-15: judge complete — all pack hashes verified, phases A-D
  in order, X read first per the parity rule. Weighted totals:
  X 60/60, Y 52/60 — X strictly stronger on the rubric. The decisive
  deduction: a mechanically-checkable record-vs-summary drift in
  pack Y (journal shape tallies contradicting its own staged
  capsule). Judge's Phase-D disclosure: suspected a paired trial on
  complementary bands; states the suspicion influenced no score.
  Assignment stays sealed until the verdict assembly (measurer still
  out).
- 2026-08-15: measurer complete — mechanical tally CONTROL 1 (M3),
  CAPSULE 1 (M4), five ties. Full enumerations preserved in
  consumption-trial/ alongside the judge report.

## VERDICT (§9, assembled 2026-08-15)

**NULL — "no recognisable advantage."** Neither arm reached ≥4 of 7
mechanical metrics (tally 1–1–5); the judged layer went strictly to
the capsule arm (60 vs 52). A split across layers is, by
pre-commitment, the null verdict — not a debate.

**Assignment unseal**: X = T2B = CAPSULE (judged 60/60, won M4);
Y = T2A = CONTROL (judged 52/60, won M3). Seal hash verified:
8cda05833e90ee94ee3996b5a6f0223d95e2f79eba73b38d5d65225ade070124.

**Deviation ledger**: D3 — T2A's disclosed un-ledgered connectivity
probe; T2B's harness-timeout kill with clean retry; the measurer's
M2 normalization choice (grounded in the protocol's own method
citation; the strict alternative reading would have flipped M2 to
the capsule arm — tally 1–2–4, verdict unchanged). Noted per §11.4 —
the judge's Phase-D structural suspicion, disclosed, with no score
influence claimed; the decisive deduction is mechanically checkable
regardless. No D1, no D2. Run valid.

**Secondary observations (recorded, no verdict weight)**: (1) The
control arm fell into the record-vs-summary-drift trap in its
literal form — its journal's shape tallies contradict its own staged
graph (M4 #43/#44/#67; the judge found it independently and it
decided the judged layer). The capsule arm — briefed on exactly that
failure family — reconciled perfectly everywhere mechanically
checkable. (2) The capsule arm's unverified-claim rate was roughly
half the control's (0.066 vs 0.119) — M4 is the record-honesty
metric. (3) The control arm's M3 win traces mostly to the capsule
arm's minted observedAsset IRI design choice, robust to sensitivity
but a design cost, not a discipline failure. (4) Both arms were
otherwise near-indistinguishable: same N, both conforming, zero
staged debt, ceilings respected, honest zero-arc findings. The
protocol's own counterweight 6 predicted this: the shared method
already equalizes most of the trap surface, so the null is a real
finding about where the value does NOT live — and the directional
signal (journal-vs-graph honesty) points at where it does.
