# Polymath Benchmark — the Sealed Arc-Recovery Protocol

**Committed BEFORE any ingester runs** (doc 15 §4's pre-commitment
requirement; cross-corpus synthesis §5.3's "sealed benchmark — after the v3
freeze"; the freeze is VOCAB-NOTE-KH3, 2026-08-13). This file is the public
half of the trial: the task, the source split, the blinding rules, the
scoring rubric, the deviation classes, and what counts as a win are fixed
here. The private half — the expected-arc registry — was written first and
sealed; its hash is recorded in §7. Nothing in either half may be adjusted
after the first ingester session launches. Any deviation must be reported
under the classes in §5.

## 1. The trial in one paragraph

Polymath1 (the 2009 Gowers–Tao collaborative proof of the density
Hales-Jewett theorem) is a laboratory case of understanding-formation in
public: every thought that led to the proof is on the record, in order, in
blog comments. A COLD ingester harvests the chronological threads with the
frozen v3 know-how vocabulary and then synthesizes arcs (the ARCS-1
two-stage pattern: harvest first, arc synthesis as its own pass). A JUDGE
then compares the recovered arc structure against an expected-arc registry
that was sealed before the ingester ran, built ONLY from retrospective
sources the ingester never sees. The trial tests whether the machinery can
recover: an approach initially promising; an objection weakening it; a
lemma changing what's possible; an approach branching; an
initially-peripheral idea becoming central; the group regarding the
proposition as established; and abandoned approaches retained as know-how.

## 2. The source split (the contamination contract)

Two disjoint diets. The whole trial's validity rests on this table, so it
is exhaustive: a URL's side is where it is listed, and anything unlisted is
forbidden to the ingester by default.

### 2a. INGESTER side — chronological threads, the complete allowlist

The ingester may fetch these URLs and NOTHING else. No search engines, no
wiki, no other blog pages, no archives of any other date, no repository
access, no sources dated after 2009-03-30. Read in the order below
(chronological by posting date; note the deliberate exception that thread
"1050-1099" opened after "1100-1199" — the record's own quirk, preserved).

| # | URL | date | comments | numbered range |
|---|-----|------|----------|----------------|
| 1 | gowers.wordpress.com/2009/01/27/is-massively-collaborative-mathematics-possible/ | Jan 27 | 247 | (rules/context) |
| 2 | gowers.wordpress.com/2009/01/30/background-to-a-polymath-project/ | Jan 30 | 20 | (context) |
| 3 | gowers.wordpress.com/2009/02/01/why-this-particular-problem/ | Feb 1 | 2 | (context) |
| 4 | gowers.wordpress.com/2009/02/01/a-combinatorial-approach-to-density-hales-jewett/ | Feb 1 | 221 | 1–199 |
| 5 | terrytao.wordpress.com/2009/02/05/upper-and-lower-bounds-for-the-density-hales-jewett-problem/ | Feb 5 | 101 | 200–299 |
| 6 | gowers.wordpress.com/2009/02/06/dhj-the-triangle-removal-approach/ | Feb 6 | 71 | 300–399 |
| 7 | gowers.wordpress.com/2009/02/08/dhj-quasirandomness-and-obstructions-to-uniformity/ | Feb 8 | 118 | 400–499 |
| 8 | terrytao.wordpress.com/2009/02/11/a-reading-seminar-on-density-hales-jewett/ | Feb 11 | 38 | 600–699 |
| 9 | gowers.wordpress.com/2009/02/13/dhj-possible-proof-strategies/ | Feb 13 | 118 | 500–599 |
| 10 | terrytao.wordpress.com/2009/02/13/bounds-for-the-first-few-density-hales-jewett-numbers-and-related-quantities/ | Feb 13 | 103 | 700–799 |
| 11 | gowers.wordpress.com/2009/02/21/to-thread-or-not-to-thread/ | Feb 21 | 3 | (procedural) |
| 12 | gowers.wordpress.com/2009/02/23/brief-review-of-polymath1/ | Feb 23 | 119 | 800–849 |
| 13 | gowers.wordpress.com/2009/03/02/dhj3-851-899/ | Mar 2 | 113 | 851–899 |
| 14 | terrytao.wordpress.com/2009/03/04/dhj3-900-999/ | Mar 4 | 110 | 900–999 |
| 15 | gowers.wordpress.com/2009/03/10/problem-solved-probably/ | Mar 10 | 133 | 1000–1049 |
| 16 | terrytao.wordpress.com/2009/03/14/dhj3-1100-1199-density-hales-jewett-type-numbers/ | Mar 14 | 118 | 1100–1199 |
| 17 | gowers.wordpress.com/2009/03/16/dhj3-and-related-results-1050-1099/ | Mar 16 | 137 | 1050–1099 |
| 18 | terrytao.wordpress.com/2009/03/30/dhjk-1200-1299-density-hales-jewett-type-numbers/ | Mar 30 | 91 | 1200–1299 |

Total: 18 pages, ~1,863 comments (counts verified live 2026-08-13; comment
counts include unnumbered meta-comments — the numbered research comments run
1–1299). Post-terminus write-up threads (May 2009 – Jan 2010) are EXCLUDED:
the trial's window closes with the DHJ(k) generalization thread.
`gowers.wordpress.com/2009/02/04/quick-question/` (16 comments) is EXCLUDED
as unclassified (absent from the wiki's own thread ledger; relevance
unverified); adding it would be a class-D2 deviation.

If a URL rots, the SAME content via web.archive.org is permitted
(class-D3, record the substitution). WordPress serves all comments on one
page for these posts; if pagination appears, fetch all pages of a listed
URL (still one allowlist item).

### 2b. SEAL side — retrospectives (ingester-FORBIDDEN, judge-required)

1. Gowers, "Polymath1 and open collaborative mathematics" (2009-03-10).
2. Gowers, "Can Polymath be scaled up?" (2009-03-24).
3. Nielsen, "The Polymath project: scope of participation" (2009-03-20).
4. Nielsen, "Update on the polymath project" (2009-02-09).
5. D.H.J. Polymath, "A new proof of the density Hales-Jewett theorem",
   arXiv:0910.3926 / Annals of Math 175 (2012).
6. Polymath wiki: Timeline page; Polymath1 page; Hyper-optimistic
   conjecture page (participant-curated — classified seal-side because
   hindsight-organized).
7. Cranshaw & Kittur, CHI 2011 ("lessons from a successful online
   collaboration in mathematics").
8. Martin et al., WWW 2016 ("Internet Collaboration on Extremely Difficult
   Problems").
9. Varshney, CI 2012 ("Toward a Comparative Cognitive History").
10. (Cited-not-quoted, paywalled: Gowers & Nielsen, Nature 461:879; Gowers's
    chapter in An Irregular Mind, 2010.)

### 2c. Sealer's own contamination disclosure

The sealer fetched, at survey level, these chronological-side items: post
bodies/summaries of allowlist items 4 and 15; existence + comment-count
checks of items 5 and 14; blog monthly-archive metadata (titles, dates,
counts) for gowers 2009/01–03 and terrytao 2009/02–03. No other
chronological comment content was read. Seal arc-interior claims cite
seal-side sources only; allowlist items 4 and 15 are cited in the seal only
to frame the launch rules and the terminus event. The sealer's complete
fetch ledger (31 calls) is in §9.

## 3. Conditions and blinding

- **Ingester**: a cold agent (Sonnet-class — the program's standard trial
  consumer; the coordinator must record the exact model BEFORE the run and
  use the same model for every session). It receives: the allowlist table
  verbatim, bridge access to a FRESH benchmark capsule seeded with the v3
  seed export (1151 quads, per VOCAB-NOTE-KH3), and a harvest brief. It is
  told it is ingesting a historical mathematical collaboration for the
  corpus program. It is NOT told a sealed benchmark exists, NOT given this
  protocol, NOT given repo access, and NOT given search tools.
- **Ingester brief core (pre-committed, verbatim)**: "Ingest the following
  discussion threads in the order listed. Record what you find with the
  know-how vocabulary in the capsule: episodes, onsets, observations,
  claims with evidence. Every recorded statement must carry an anchor: the
  thread URL plus comment number(s) (participants numbered their research
  comments) or the post body. After the harvest sessions, run a synthesis
  pass over your own recorded observations: identify the arcs of
  understanding — how questions opened, pivoted, and settled — with
  ordered membership, pivot evidence, and what became settled or automatic;
  mark each arc's terminus character honestly, and record what was
  abandoned as retained know-how with its reason. Do not import outside
  knowledge: if you believe something about this history that the record in
  front of you does not show, it does not go in the capsule."
- The brief writer adds only mechanics (bridge paths, session boundaries)
  — never content hints. Since the sealer wrote both the seal and this
  brief core BEFORE any run, brief-writing cannot leak the seal.
- **Judge**: a separate agent, spawned only after the ingester's capsule +
  arc synthesis are frozen (exported, hashed, archived). The judge gets:
  this protocol, the frozen ingester output, BOTH source lists, seal-dir
  read access, and a fetch budget (≤40) for anchor checks. The judge must
  verify the seal file's SHA-256 (§7) before opening it.
- **Order blinding (hash-parity, house style)**: the seal hash's first hex
  digit is EVEN, so the judge grades seal entries in registry order; had it
  been odd, reverse order. (Fixes grading order mechanically, outside
  anyone's discretion, and is recorded before any run.)

## 4. Pre-committed scoring

The judge proceeds in four phases, in order, no backtracking:

- **Phase A — normalize, seal unseen.** Read ONLY the ingester output.
  Reduce it to a normalized registry: each recovered arc as
  onset / pivot / terminus / establishment-status / anchors. Freeze Phase A
  in writing before opening the seal. (This is the analogue of blind
  judging: it prevents reading seal content into vague ingester prose.)
- **Phase B — match and grade.** Open the seal (hash-check first). For each
  seal arc, grade:
  - **RECOVERED**: onset, pivot, AND terminus each match the seal entry
    (same underlying events, within the seal entry's own recovery-note
    tolerances), each with ≥1 valid anchor; establishment status correct.
  - **PARTIAL**: ≥2 of the three elements match, anchored; no
    establishment-status error on this arc.
  - **MISSED**: fewer than 2 elements match.
  Grade each seal NEGATIVE: **correct** (recorded as
  abandoned/open/retained, or absent) vs **failed** (asserted with
  establishment semantics). Grade the three probes per the seal's probe
  index.
- **Phase C — anchor audit.** For every arc graded RECOVERED or PARTIAL,
  and for every ingester statement flagged in Phase D, open the cited
  thread and verify the anchor supports the statement. An arc element whose
  anchors fail drops out and the arc is re-graded. Anchors are the
  anti-pretraining instrument (§8.1): unanchored knowledge scores nothing.
- **Phase D — surplus adjudication.** Ingester arcs matching no seal entry:
  verify their anchors. If the record genuinely supports one, report it as
  **plausible-novel** — a finding about the SEAL's gaps (retrospectives
  demonstrably under-record onsets — ARCS-1), NOT a penalty. If anchors
  fail or the arc contradicts a HIGH seal negative, it is **HALLUCINATED**
  (penalty class).
  - **Hallucinated-established-claim** (zero-tolerance class): any
    statement in the ingester's record carrying establishment semantics
    (settled / became-automatic / proof-complete) that Phase C refutes.

**Headline score** = (#RECOVERED) + 0.5·(#PARTIAL) − 1.0·(#hallucinated
arcs), over the 8 seal arcs.

## 5. Deviation classes

- **D1 — invalidating**: ingester fetches ANY non-allowlist URL or is given
  search/repo access; anyone reads the seal before Phase A freezes; seal
  hash mismatch; scoring rules or success criteria edited after first
  launch; ingester learns of the benchmark. Result: run void, reported as
  such; the seal survives unopened only if the ingester never ran — a
  leaked seal is spent (this trial is one-shot; a new seal would need a new
  sealer and a fresh design).
- **D2 — recorded, verdict stands with caveat**: session chunking differs
  from plan; partial thread coverage from fetch failures (record exactly
  which comments were lost); an [EG] seal quote fails the judge's
  re-verification (drop the quote, re-grade that arc on remaining
  evidence); adding the excluded "quick question" post.
- **D3 — noted only**: archive.org substitution for a rotted URL (same
  content); infrastructure retries; cosmetic tool changes.

## 6. Ingestion strategy (feasibility, decided now)

~1,863 comments across 18 pages; research comments are LaTeX-dense and
long. Sealer's estimate: 250–350k words ≈ 350–500k tokens of raw source —
far beyond one context. Therefore:

- **Chunked chronological sessions with capsule persistence** — the
  program's native mode (the capsule, not the context, is the memory).
  Plan: 8 harvest sessions of 2–3 threads each (~150–260 comments per
  session), strictly in allowlist order, each session ending with its
  observations applied and conforming; then ONE synthesis session (the
  ARCS-1 pattern: arcs are syntheses over recorded observations, zero new
  capture machinery), then export + freeze.
- **CORE fallback variant** (if budget forces it, decide BEFORE the run,
  record which variant ran): drop threads 5, 10, 16, 18 (the numbers-branch
  and DHJ(k)-numbers threads), keeping the proof track + reading seminar +
  one branch thread (14). Pre-committed grading change: the seal's
  numbers-branch arc is then graded on branch-existence/relation only.
- Ingester fetch budget ≤60 (18 pages + re-fetches); polite pacing.

## 7. The seal

- Seal file: `SEAL-polymath-arc-registry-2026-08-13.md`, held OUTSIDE every
  repository at `/home/codex/polymath-seal/` (with a README stating the
  no-read rule). Never committed, never copied into any path an ingester
  brief references.
- **SHA-256**:
  `240eda891571d2eef89abf6abd5d4d792bee7165012184bc007f63092374ee18`
- Public shape (content stays sealed): **8 expected arcs** (6 HIGH
  confidence, 2 MEDIUM), **5 expected negatives** (3 HIGH, 2 MEDIUM),
  **3 probes** (peripheral-becomes-central; abandoned-approaches-retained;
  chronology traps), **1 sealed prediction** about terminus surfaces, and a
  **6-item retrospective-disagreement ledger** (the retrospectives
  disagree on participation and comment counts; recorded as trial material,
  not smoothed).
- Every seal quote is provenance-marked ([VV] sealer-verified verbatim vs
  [EG] extraction-grade); the judge re-verifies [EG] quotes before use.

## 8. Success criteria (sealed before the run)

Over the 6 HIGH-confidence seal arcs, with negatives and probes as gates:

- **PASS** requires ALL of:
  1. ≥4 of 6 HIGH arcs graded ≥ PARTIAL;
  2. ≥2 of 6 HIGH arcs graded RECOVERED;
  3. ZERO hallucinated-established-claims;
  4. ≥3 of 5 negatives correct;
  5. headline score ≥ 3.0.
- **STRONG PASS**: PASS, plus ≥5/6 HIGH arcs ≥ PARTIAL, ≥3 RECOVERED, the
  peripheral-becomes-central probe ≥ PARTIAL, ≥4/5 negatives correct, and
  zero hallucinated arcs of any kind.
- **FAIL**: anything below PASS. Reported plainly; doc 15 §6's
  falsification clause engages for this evidence tier.
- **NULL/VOID**: any D1 deviation.

Why these numbers are honest: ARCS-1 showed arc ONSETS are the structurally
hard part (systematically unrecorded under a decision lens) — demanding all
three elements on every arc would test hindsight, not machinery, so
majority-partial with a two-full floor is the demanding-but-fair bar. The
zero on hallucinated-established-claims is not negotiable because
establishment discipline (the ≥2 rule, the refusal culture) is the
program's spine — one fabricated "settled" poisons the capsule's entire
value proposition. Negatives are gated at 3/5, not 5/5, because two are
graded MEDIUM on the seal's own evidence and the seal may lose those
honestly (§4 Phase D lets anchored ingester evidence beat a MEDIUM seal
entry).

## 9. Counterweights — what a win would NOT prove

1. **Pretraining contamination is real and unremovable.** Polymath1 is the
   most-written-about mathematical collaboration in history; the ingester
   model has almost certainly absorbed retrospectives in training. Anchor
   discipline (§4 Phase C) converts the question from "does the model know
   this story" to "can the machinery carry the story with evidence
   attached" — but a win here CANNOT be claimed as cold-corpus arc-recovery
   ability. Contamination softens the negatives too (training data warns
   about Austin's proof). What stays genuinely hard: comment-level
   anchoring, establishment honesty, expressibility in frozen v3 terms, and
   cross-session continuity through the capsule. Claims stop there.
2. **One corpus, one genre, n=1.** A famous, single-venue, well-curated,
   all-human, seven-week mathematical collaboration. No generality claim to
   kernel-style multi-venue records, email genres, machine-participant
   corpora, or decade-long arcs.
3. **The seal is winner's history.** Built from retrospectives, it inherits
   their biases; arcs invisible to retrospect are invisible to this trial
   (ARCS-1's onset finding cuts against the seal itself). Phase D's
   plausible-novel channel partially compensates but is judged by one
   agent.
4. **A win does not validate untouched vocabulary layers**: machine
   participants, authority regimes, policy citizens — none are exercised by
   a 2009 all-human public-record corpus (public-record regime only).
5. **The sealed character is spent on this run.** Win or lose, re-running
   against the same seal proves nothing (the second ingester's lineage
   can't be isolated from this trial's artifacts). One shot; report what
   happens.

## 10. After the verdict

The judge's report: per-arc grades with anchor evidence, negative and probe
outcomes, plausible-novel findings (seal gaps), deviation ledger, verdict
against §8. James spot-checks at his leisure (the gold standard remains the
owner recognizing real understanding-formation in the recovered arcs).
Product findings (bridge friction, vocabulary couldn't-says from a
mathematical corpus) flow to the distiller ledger regardless of verdict —
a FAIL with clean couldn't-says is a useful result, per the program's
null-result doctrine.

## Appendix: sealer's fetch ledger (31 calls, ≤50 budget, 2026-08-13)

WebFetch (26): gowers launch post; wiki Main_Page; wiki Timeline (summary +
raw); wiki Polymath1; gowers "Polymath1 and open collaborative mathematics";
nielsen scope-of-participation; nature.com/articles/461879a (paywall
redirect, abandoned); gowers "Problem solved (probably)"; cs.cmu.edu
dhj.pdf; cs.cmu.edu cranshaw_kittur.pdf; springer ch.20 pdf (paywall
redirect, abandoned); arxiv.org/abs/1205.7084; cs.cornell.edu
www16-polymath.pdf; arxiv.org/pdf/1204.3534; gowers archives 2009/01,
2009/02, 2009/03; terrytao archives 2009/02, 2009/03; terrytao Feb 5
thread (existence/count); terrytao Mar 4 thread (existence/count); nielsen
category/polymath1; gowers "Can Polymath be scaled up?"; nielsen
update-on-the-polymath-project; wiki Hyper-optimistic_conjecture.
WebSearch (5): wiki/timeline discovery; Cranshaw–Kittur PDF; Gowers
Irregular-Mind chapter (×2 variants); polymath thread listing.
All public sources; PDFs text-extracted locally (pypdf) for verbatim
verification.
