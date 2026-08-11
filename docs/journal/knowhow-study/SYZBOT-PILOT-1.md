# SYZBOT-PILOT-1 — the first artifact-interleaved foreign-corpus harvest

**Date**: 2026-08-11. **Operator**: syzbot pilot harvest session, per the
density-sample memo (`/home/codex/doxabase-private/knowhow-review/syzbot-sample-memo.md`,
its pilot filter and access methods treated as law) and the scout memo's
conditions. Machinery exercised: ARCS-1 arc model + VOCAB-NOTE-KH2 v2
vocabulary (`kh:Episode`, `kh:Arc`, onset shapes, `kh:pivotQuote`,
`kh:becameAutomatic`, `kh:leadsTo`, `kh:showsFormationOf`).

**Hard rules honored**: sanctioned access only (syzkaller.appspot.com public
pages + lore.kernel.org t.mbox.gz data endpoints, Wget/1.21.3 UA, 1.4s pace,
every operation ledgered in `ops_ledger.jsonl` before firing, budget 170
enforced in `fetch.py`); NO person-model claims about anyone (owner has not
set the living-maintainers posture — episodes are role-based, names only where
an episode is meaningless without them, quotes verbatim); machine participants
noted distinctly in episode prose, no kh: terms invented for them (the
vocabulary gap is journaled below instead).

## Setup log

- `/home/codex/syzbot-knowhow/` created; `uv venv venv`; doxabase 0.2.0 wheel
  installed from `/workspaces/doxybase/dist` (wheel verified fresher than the
  repo's last commit — no rebuild needed; repo untouched).
- `bridge.py` copied from the AIS study — the only door to the capsule.
- Capsule seeded (`DoxaBase('capsule.sqlite')`).
- `kh-vocab-seed.trig` imported via `import_bundle`. First call failed with the
  targeted error (`kind` required) — the error taught the fix in one step, as
  designed; `kind="trig"` imported 731 triples (shapes 258, ontology 473).
- `validate_graph scope=all`: **conforms, 0 results**. `kh:Episode` and
  `kh:Arc` verified present with their v2 supersede-retain comments.

## Corpus-separation note

Nothing in this session writes to any capsule other than
`/home/codex/syzbot-knowhow/capsule.sqlite`. The Enron pilot's directory was
consulted READ-ONLY for its staging method (observations.py / stage_a.py /
stage_b.py pattern reused) and later for the economics comparison.
`ENRON-PILOT-1.md` does not exist at harvest time — that session has not
finished its journal; economics comparison uses its bridge log and
pipeline_counts.json read-only, flagged as provisional.

## Network-operation ledger (running)

- op 1: `/upstream/fixed` full listing (7.45 MB, one request, no pagination —
  reproduces the sample memo's finding; 7,280 rows parsed, 5,970 with extids).
- ops 2-69: 68 bug pages. Selection: last-crash-days recency proxy (the
  memo's method), subsystem spread capped at 9 per subsystem across the
  memo's recommended set (net, wireless, usb, mm, kvm, bluetooth, netfs/fs,
  mtd, media + adjacent ext4/udf/hfs/sound/input/wpan/can/bridge/io-uring);
  all 22 of the sample memo's bugs found in the listing and EXCLUDED so the
  filter-precision test runs on fresh N.
- ops 70-142: 73 distinct thread mboxes (t.mbox.gz), deduplicated across bugs
  (4 threads shared by two bugs each — the fetch plan deduped them).
- Zero anti-bot challenges anywhere, again reproducing the memo's operational
  finding. 142/170 used at end of fetch phase; 28 held in reserve for
  follow-ups.

## Screening result (two-tier filter, N=68 fresh candidates)

| Outcome | Count |
|---|---|
| Tier 1 (>=2 [PATCH rows) — likely-A | 30 |
| Tier 2 (one PATCH thread, >=3 msgs) | 17 |
| Skip — single PATCH thread, <3 msgs | 17 |
| Skip — no PATCH row at all | 4 |

Skip rate 21/68 = 31% (vs the memo's 14% at N=21 — the memo's skip rule was
narrower: zero-reply only. Under the memo's own rule my skips would count the
zero-reply subset only; recomputed in the stats section below.)

Grading and episode selection: 4 parallel graders over per-lifecycle digests
(mbox parsed, diffs stripped, quotes trimmed), each under the shared
GRADING-BRIEF.md (grades per the memo; verbatim-quote discipline; role-based
prose; machine actors listed with adopted/dismissed/relayed outcomes). Every
quote mechanically re-verified against the digests before recording.

(continued after grading)

## Interruption note (honest record)

A quota outage cut the session mid-grading: the batch1/batch4 graders had
JUST written their files (both parsed valid and passed mechanical quote
verification afterward); the batch2 grader died after reading all 12 digests
but before writing, and was resumed from its transcript (the parting-notes
resumption method — it worked). No capsule state was affected; the bridge and
staged-revision machinery carried no debt across the outage.

## Harvest record (batches 1/3/4 = 35 lifecycles; batch2 pending at this line)

- 56 observations recorded (46 episode observations from 24 A/B lifecycles,
  5 arc onsets, 5 arc summaries). Every quote mechanically re-verified
  against the digests (whitespace-normalized) before recording; two
  duplicated formation moments from the shared hfs thread (217eb327/bc70a12e)
  recorded once.
- **Batch A staged+applied**: 46 kh:Episode nodes, 288 triples, conforms.
  (Bridge lesson repeated: apply_staged_revision wants `iri`, not
  `revision_iri` — the targeted error taught it in one step.)
- **Batch B (arcs) — the gate earned its keep**: first staging of the five
  kh:Arc nodes FAILED validation with 20 MinCount violations, because
  dual-typing kh:Arc as rc:Pattern (the ARCS-1 modeling decision) pulls in
  the base ontology's Pattern shape: patternTarget, patternText,
  rc:rationale, rc:summary are mandatory. The kh-vocab seed's ArcShape alone
  does not tell you this; the Enron pilot evidently hit the same wall (its
  bridge log shows 3 stagings for 2 applies). Restaged with real Pattern
  content per arc — not filler; the patternText fields are the arcs'
  transferable pattern statements — applied cleanly: 81 triples, conforms.
  The failed staging closed via stage_revision kind=review_decision,
  decision=superseded, allow_mutation_target=true (the tool's refusal text
  taught the flag), rationale preserved. Zero staged debt confirmed
  (plan_staged_revision_recovery: 0 rows).
- The five arcs: rt-unlock-rcu-ordering (reattribution-before-fix;
  Decoded-by trailer noted); hfs-bnode-centralized-hardening
  (centralize-at-the-chokepoint; onset honestly marked in-corpus arrival);
  machine-authorship-norm (norm-into-tooling — becameAutomatic is LITERAL:
  'Now the sending mechanism will automatically set the right From: line');
  kvm-asyncpf-diagnosis-to-citation (arc duration measures embodiment, not
  understanding); bridge-xstats-bounded-fill (review-one-layer-further;
  patchwork narrated-merge terminus surface demonstrated in-capsule).
- **Deliberate non-promotions**: kcov/PREEMPT_RT (90984d37) — the richest
  formation lifecycle in the corpus (draft→v7, an AI-sourced causal claim
  publicly refuted by the RT maintainer, the AI's retraction reported back
  into the thread) — is mid-arc at capture (no apply notice; cc:stable
  discussion open), so no honest becameAutomatic exists; episodes recorded,
  arc NOT promoted (ARCS-1 'one arc mid-flight' + Enron GE-standardization
  precedent). can/bonding (8ed98cbd) left unpromoted: complete story but a
  single diagnosis pair as spine — arc-count discipline.

## Batch2 integration (post-resume)

The resumed grader delivered batch2.json; verify_quotes.py: ALL OK (all four
batches). 15 further episodes curated from its 8 A/B lifecycles (the kcov
sibling digest contributed ONE distinct episode; its other two duplicated the
already-recorded 90984d37 pair and were dropped — the two independent graders
of the shared lifecycle agreed on grade A and on which moments mattered).
Batch C staged + applied: 99 triples, conforms. Standouts: the TERMINUS
REVERSAL (hid/asus: maintainer applies v1, a cross-subsystem concurrency
objection lands hours later, 'Now dropped from the queue.' — an applied
decision resumes being a decision); churn priced against AI-report volume
('Given the amount of work we currently have with various AI reports, I will
keep it this way to avoid unnecessary noise'); a reviewer's 15-minute
spec-citing self-correction becoming the v3 commit message's opening line.

## Final capsule state

- 77 observations (61 episode + 5 onset + 5 arc-summary + 3 stats + 3 meta);
  61 kh:Episode nodes; 5 kh:Arc (dual-typed rc:Pattern) across three applied
  staged revisions (A: 288, B: 81, C: 99 triples).
- validate_graph scope=all: conforms, 0 results (checked after every apply
  and at close). plan_staged_revision_recovery: 0 rows — zero staged debt
  (one superseded-closed row with rationale, per the review_decision route).
- export_preflight: scanner clean; shareability review required-not-completed
  (correct — owner has not reviewed; nothing exported).
- Retrieval sanity: arcs and episodes findable by natural queries;
  describe_resource returns the machine-authorship arc with full Pattern +
  Arc fields.

## Grade distribution and stats (recorded as observations)

A=11, B=21, C=15 of 47 graded (68% A+B; distinct lifecycles 44 after
shared-thread dedup). Tier1->A = 33% raw / 43% version-aware; Tier1->(A|B)
= 83% — the memo's 8/8 was small-N optimism; full decomposition (incl. the
two capture-artifact C grades) in the stats_filter observation and META-RQ2.
Machine participation in stats_machine: Sashiko 21%, patchwork-bot 26%,
AI-assisted patches from three assistant vendors, plus four machine roles
the sample memo had not seen (trailer-only analysis sources, AI reporters
seeking admission, anticipated-future-scrutiny, churn-pricing).

## Network-operation ledger — CLOSED

142 of 170 operations used (1 listing + 68 bug pages + 73 thread mboxes);
28 unused; zero anti-bot challenges; zero failed fetches; zero follow-up
fetches needed. Every operation logged to ops_ledger.jsonl BEFORE firing.
Combined with the sample session's 52, the sanctioned-endpoint route is now
194-for-194 clean.

## Friction (product-relevant, domain-stripped)

1. **History rows outrank live nodes in search** — reproduced: the failed
   arc staging's validation-result rows rank above the live arc node for its
   natural query (rank 0-3 vs 4). DISTILL-2 logged this once; now
   twice-sighted -> earns its product-ledger entry per the counting rule.
2. **kh:Arc ⊑ rc:Pattern staging trap**: the seed's ArcShape does not
   mention the four rc:Pattern MinCount fields its dual-typing pulls in from
   base shapes; both foreign-corpus pilots hit it (Enron's 3-stagings-for-
   2-applies pattern, this pilot's 20-violation staging). A one-line note on
   the ArcShape (or a kh: composite shape) would save every future harvest
   one failed staging.
3. **apply_staged_revision takes `iri`, stage responses emit
   `revision_iri`** — the name mismatch costs one targeted error per fresh
   session (it taught in one step, as designed, but the asymmetry is free to
   fix).
4. **review_decision requires allow_mutation_target for current staged
   rows** — right default, and the refusal text teaches the flag; noting
   only that the Enron-style probe-close path goes through it.
5. Grader-scale friction: two graders died writing at a quota cliff and one
   resumed cleanly from transcript — the parting-notes resumption method
   held; worth keeping briefs re-runnable and outputs single-file-atomic.

## Verdict

The harvest validates the sample memo's GO: the corpus is dense (68% A+B at
N=47), the vocabulary holds with the four named strains (META-RQ1), the
economics beat Enron per unit of total effort (META-RQ3), and the filter is
real but is a formation-bearing filter, not an A-filter (META-RQ2). The
machine-participation layer is richer than either scout pass saw and is
where the next vocabulary decision (owner-gated) is needed.
