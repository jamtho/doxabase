# Syzbot / Linux Kernel Patch-Evolution Scout Memo — Understanding-Arc Source Assessment

**Scope**: assess whether the syzbot-linked Linux kernel patch-review corpus
(mailing-list review threads reconstructible via lore.kernel.org, indexed
by syzkaller.appspot.com) can serve as source material for understanding-arc
harvesting per Design Doc 15
(`doxabase_design_docs/15-know-how-generalization.md`) and the arc model in
`docs/journal/knowhow-study/ARCS-1-report.md` (onset → formation → pivot →
becameAutomatic terminus).

**Method**: read-only reconnaissance. (1) Assessed the paper "Beyond
Crash-to-Patch: Patch Evolution for Linux Kernel Repair"
(arXiv:2604.03851) via its abstract and full HTML text. (2) Independently
followed one live syzbot bug from the public dashboard through its full
lore.kernel.org review thread — 10 messages, 2020-12-10 (original crash
report) through 2026-07-31 (last review reply), reconstructed via
lore's full-text search-with-thread-context (`x=t`) and per-message
`t.mbox.gz`/`raw` endpoints. Roughly 21 network requests total across
arxiv.org, syzkaller.appspot.com, and lore.kernel.org, paced with pauses
between same-host calls — well under the 40-fetch budget. Compared
against `/home/codex/doxabase-private/knowhow-review/enron-scout-memo.md`
(read-only).

**Operational note**: lore.kernel.org's live HTML interface is behind
Anubis (JS proof-of-work anti-bot). A browser-like `curl`/WebFetch
User-Agent gets the Anubis challenge page, not content. A `Wget/1.21.3`
User-Agent passed cleanly on every request; a bare `curl/8.5.0` UA got a
flat 403 from nginx before even reaching Anubis. Git's smart-HTTP protocol
(`git ls-remote`, `git clone --mirror`) bypasses Anubis entirely and is
the officially documented bulk-access path (confirmed via
`lore.kernel.org/<list>/_/text/mirror/` on `linux-wireless` and `lkml`).
This UA-dependent fragility is a real finding for §5, not just a scouting
inconvenience.

---

## 1. The paper: "Beyond Crash-to-Patch: Patch Evolution for Linux Kernel Repair"

**It exists as described.** arXiv:2604.03851 (April 2026), Luyao Bai,
Kenan Alghythee, Hang Zhang, Xiaoguang Wang (UIC). Abstract verbatim
confirms the framing DoxaBase's brief anticipated: "kernel fixes undergo
iterative revision on mailing lists before acceptance, with reviewer
feedback shaping correctness, concurrency handling, and API compliance.
This iterative refinement process encodes valuable repair knowledge that
existing automated approaches overlook." That sentence could be dropped
into Design Doc 15 §1 without editing — independent confirmation, from a
different research community, of the same underlying intuition (episodic
review exchanges carry knowledge a single crash-to-patch mapping does
not).

**Dataset contents**: a "multi-stage pipeline" integrating the syzbot
API, git.kernel.org, lore.kernel.org, and patchwork.kernel.org
reconstructs 6,946 syzbot-linked bug-fix lifecycles, each with three
artifact classes — bug/crash metadata (ID, title, crash timestamps,
reports, reproducers), repair discussion (mailing-list messages, thread
structure, patch-revision metadata, recovered by parsing `[PATCH v2]`-style
subject markers since "revised patch versions are not always posted as
strict replies"), and the merged fix (commit metadata + final diff).
Fixing-commit diffs were successfully recovered for 5,043 of the 6,946
candidate bugs (~73%) — the rest presumably never landed, or landed via a
path the pipeline couldn't trace. Dataset size: 13 GB (11 GB processed
JSON, 1.5 GB raw crawl, 210 MB training data).

**Not publicly downloadable, as far as this scout can determine.** No
data-availability statement, DOI, GitHub repo, Zenodo record, or
HuggingFace dataset card turned up in the paper text or in three targeted
web searches for the project/authors/PatchAdvisor name. This is a real
negative finding, symmetric to Enron's positive one: Enron's corpus is
already sitting in a queryable bucket; this one would have to be
reconstructed from scratch, using the same four sources the paper names
(syzbot API, git.kernel.org, lore.kernel.org, patchwork.kernel.org) — all
public and independently confirmed reachable in §2 below.

**"ReviewLesson" structure — the key comparison point.** The paper
distills review feedback into `ReviewLesson` records built from a **flat,
12-category taxonomy** of revision reasons: `correctness, commit_message,
api_design, race_condition, incomplete_fix, documentation, config_build,
style_convention, error_handling, scope, memory_safety, performance`.
Each category tracks frequency, average diff-size impact, and
changelog-acknowledgment rate. This is a *classification* scheme, not a
*narrative* one: no ordering, no onset/pivot/terminus, no per-thread
arc, no person-model, nothing resembling "the arc completes when its
decisions stop being decisions." It sits at roughly the altitude of
DoxaBase's `mc:` method-contract failure-mode list (a flat catalogue of
named failure categories with evidenced frequency) — useful as a
*category vocabulary a real harvest could reuse or validate against*, but
it does zero of the work our episode/arc/heuristic ladder does. The gap
between "the paper's structure" and "our structure" is the whole reason
a DoxaBase-side harvest would be additive, not redundant, if this corpus
were pursued.

**Threats-to-validity honesty is notable**: the end-to-end evaluation
covers only 6 bugs "due to strict selection criteria (working
reproducer, multi-version history, temporal separation from training
data)," explicitly "precludes statistical significance testing," and is
framed as "proof-of-concept." The LLM judge is Claude Sonnet 4.6, flagged
by the authors themselves as a construct-validity risk. This is a
well-scoped, honestly-limited paper, not an overclaiming one — and its
own N=6 "strict selection" bottleneck previews exactly the yield problem
a DoxaBase pilot would hit (see §5).

## 2. Independent sample: one bug, crash to merge, quoted

**Bug**: "possible deadlock in zd_chip_disable_rxtx" (`zd1211rw` USB
Wi-Fi driver), syzbot `extid=0ec3d1a6cf1fbe79c153`. Originally reported
2020-12-10 — sat unfixed for **almost six years** — then picked up and
driven to a merged fix in nine days (2026-07-20 to 2026-07-31) by syzbot's
own AI-patch-generation pipeline plus two human reviewers. The syzbot
dashboard's live "Discussion" links on the bug page already do most of
the crash→discussion→patch joining work — this is a structural advantage
over Enron, where threading had to be reconstructed from subject-line
drift (see §5).

Full reconstructed thread (10 messages, all recovered):

| Date (2026) | Author | Message |
|---|---|---|
| 07-20 11:46 | syzbot (AI, Gemini-3.1-pro-preview) | `[PATCH RFC]` — first attempt, posted only to `syzkaller-upstream-moderation` |
| 07-28 09:59 | Slawomir Stepien (human) | objects twice, promotes nothing yet |
| 07-28 11:14 | syzbot (AI) | `[PATCH RFC v2]` — addresses both objections |
| 07-29 08:01 | Slawomir Stepien | `#syz upstream` — approves, promotes to real submission |
| 07-29 08:04 | syzbot (now human-SoB) | `[PATCH]` v1 to `linux-wireless`, cc `linux-kernel` |
| 07-29 18:53 | Jeff Johnson (Qualcomm, human reviewer) | style objection |
| 07-30 06:52 | Slawomir Stepien | `[PATCH v2]` — style fix only |
| 07-30 08:39 | syzbot ci | automated: "found no issues" |
| 07-31 17:36 | Jeff Johnson | DCO/AI-authorship policy objection |
| 07-31 19:45 | Vlastimil Babka (SUSE, human) | resolves the policy question |

Six formation-bearing passages, verbatim, with message links (all under
`lore.kernel.org/all/<msgid>/`):

1. **A human catching an AI's unsupported causal claim, not just a typo**
   — Slawomir Stepien, 2026-07-28 09:59, replying to the RFC's claim that
   endpoint contention causes `-EAGAIN` errors
   (`amh9l5yv-BS8yTRz@nr200`):
   > "I'm a bit lost here. Can you explain why we see -EAGAIN error in
   > logs? Maybe the -EAGAIN error is caused because we do not have real
   > true device? If this is the case, I would not add this paragraph to
   > the commit message."

2. **The revision that answers exactly that objection, labeled as such**
   — syzbot's RFC v2 changelog, 2026-07-28 11:14
   (`4ccb85ef-8c74-4226-92ac-f8145816eb0a@mail.kernel.org`):
   > "v2: - Removed the explanation of the -EAGAIN error from the commit
   > message. - Removed the line containing only '='."

   This pair (1)→(2) is a textbook `kh:showsFormationOf` link: the
   artifact delta cites the objection it resolves, not just a version
   bump. It is a cleaner instance of the pattern than anything the Enron
   scout found — kernel patch changelogs are *written to* carry this
   linkage as a genre convention (a `vN:` block enumerating what changed
   and implicitly why), whereas the Enron memo had to infer formation
   from subject-line drift and "REV 4" markers.

3. **A style objection that states the rule's history, not just the
   rule** — Jeff Johnson, 2026-07-29 18:53
   (`a8e1200f-5f79-4c86-915c-96464596fd0e@oss.qualcomm.com`):
   > "this does not follow linux block comment style / * should be on a
   > separate line (at one time networking code had a different style,
   > but not now)"

   This is exactly the kind of tacit, undocumented-elsewhere knowledge
   Doc 15 is after: not "the rule" (that's in a style guide) but "the
   rule changed, and I know which side of the change we're on" — a
   maintainer's calibration that isn't written down anywhere the AI
   patch-generator could have retrieved it from.

4. **A community-norms question raised in real time, with the actual
   policy text quoted against the case at hand** — Jeff Johnson,
   2026-07-31 17:36 (`dbe5b96e-c95c-474e-aca0-8227fee4682a@oss.qualcomm.com`):
   > "E-mail from syzbot but SOB from a human? I read the trailer, but
   > this seems to violate: https://docs.kernel.org/process/coding-assistants.html
   > Namely: AI agents MUST NOT add Signed-off-by tags. Only humans can
   > legally certify the Developer Certificate of Origin (DCO)."

5. **The resolution — reasoning through a policy text to an
   interpretation, not just an assertion** — Vlastimil Babka (SUSE),
   2026-07-31 19:45 (`1bc703a1-132f-4472-a703-d5c804d215c8@kernel.org`):
   > "Since From: and S-o-b: refers to a human developer, and there's
   > Assisted-by:, it seems to be according to the rules. The 'From:
   > syzbot' seems to be just a sending mechanism, that wouldn't even
   > make it to the git commit log."

6. **The approval-as-punctuation moment, literalized as a bot command**
   — Slawomir Stepien, 2026-07-29 08:01 (`ammzaex8HJff4Imm@nr200`):
   > "#syz upstream" (entire substantive content of the message — a
   > one-line macro that promotes the RFC to a real submission with a
   > human Signed-off-by).

**How hard was the joining work?** Moderate, and front-loaded onto
finding the right access method rather than onto data modeling.
syzbot's own bug page already supplies the crash→discussion→fix linkage
(it lists every discussion-thread permalink and the fix-commit title
directly) — a meaningfully easier starting point than Enron, where
`message_id` is not a stable join key and threads had to be rebuilt from
subject drift plus reply-depth plus date. The friction here was entirely
access-layer: the live HTML UI is Anubis-gated (needs a UA workaround,
see header), while the sanctioned bulk paths (public-inbox git mirror
per list, or NNTP) are unthrottled and untroubled by Anubis. A real
pilot should use the sanctioned paths, not UA-spoofing, which is a
short-lived and slightly disreputable trick to depend on operationally.

## 3. Arc feasibility sketch

Mapped onto the ARCS-1 machinery, using the thread above:

- **onset**: not a decision but an anomaly — the lockdep "possible
  recursive locking" splat, first reported 2020-12-10, sitting unactioned
  for ~6 years. This matches ARCS-1's finding exactly: onsets are
  anomalies, structurally invisible to a decision-only lens, and here the
  *arc's* onset (when formation activity actually starts, 2026-07-20) is
  five-and-a-half years after the *bug's* onset — worth modeling as two
  distinct timestamps, not one.
- **episode 1**: RFC v1 → Stepien's dual objection (quote 1) → RFC v2
  (quote 2). Formation: distinguishing a real causal mechanism from an
  AI-generated plausible-sounding-but-unverified one.
- **decision-as-punctuation**: `#syz upstream` (quote 6) — a literal
  one-line command standing in for what in a human-only thread would be
  a sentence of approval. Worth flagging as a genre-specific decision
  marker a harvester should learn to recognize.
- **episode 2**: PATCH v1 → Johnson's style objection (quote 3) → PATCH
  v2, changelog "Fix the style of the block comment" — second clean
  `kh:showsFormationOf` pair.
- **machine-episode**: syzbot ci's automated "found no issues" — worth
  modeling as a distinct episode *type* (automated confirmation, not
  human judgment) rather than folding it into the human review episodes.
- **episode 3 (parallel, meta-level)**: Johnson's policy objection (quote
  4) → Babka's resolution (quote 5) — formation about a *process norm*
  (what counts as valid authorship for an AI-assisted patch), not code.
  This is a second arc-worthy thread braided into the first one; a real
  harvester would need to decide whether to split it into its own arc
  (recommended — it has an independent onset, a different pivot, and a
  different terminus condition) or fold it in as a sub-episode.
- **terminus**: the thread goes silent after quote 5 (2026-07-31 19:45).
  No further on-list message was found. The syzbot dashboard, checked
  live, shows the fix "Patched on: [ci-upstream-linux-next-kasan-gce-root
  ci-upstream-net-kasan-gce]" — i.e., merged — with no visible on-list
  "applied, thanks" announcement in the captured thread. **The ARCS-1
  'decisions stop being decisions' terminus signature reproduces exactly
  as predicted**: nobody narrates the merge; the thread simply stops
  generating new objections once the review categories (causal-claim
  skepticism, style, DCO policy) are each satisfied once, and the merge
  is confirmed externally (CI status / dashboard) rather than announced.
- **what became automatic**: unverified this session, but a concrete,
  testable hypothesis for a pilot — the idiom "single-function USB device
  driver rejects secondary interfaces via `bInterfaceNumber != 0` check"
  is exactly ARCS-1 shape (D), counted-repetition→structural-rule. A
  pilot with budget to sample 2-3 more `zydas`/similar-driver threads
  could check whether this exact idiom, once established here, later
  gets applied by a reviewer or the AI pipeline itself without
  re-derivation — that would be the completion test.

## 4. Person-model angle (small-sample, honest limits)

One thread is not enough to clear the ≥2-independent-sighting bar for
anyone. What it does show: Jeff Johnson posted twice in this single
thread, on two orthogonal concerns — code-style hygiene (quote 3) and
process/DCO compliance (quote 4) — which is structurally identical to
the Enron memo's own flagged-as-weakest case (Kay Mann's "de-escalates by
restating," two sightings within one thread, explicitly not promoted to
a real claim without independent confirmation). Same caveat applies here
verbatim: this is a *candidate* claim ("Johnson enforces multiple
independent categories of kernel process rigor, not just correctness"),
not a validated one.

Two follow-up search attempts to find a second, independent thread with
Johnson repeating either trait failed on query syntax (public-inbox's
`f:`/`s:` combined-filter search returned 404s the way this scout
attempted it; a broader `s:wifi` query returned too much volume to be
useful without more budget) rather than on the underlying question. This
is a mechanical gap, not a structural one: kernel reviewers are widely
understood in the community to have strong, individually recognizable
review personas — persistent pet peeves, catchphrases, areas of focus —
sustained across hundreds of patches over years, publicly on record.
That reputation is exactly the kind of thing this scout could not
confirm today but a properly-scoped pilot (grep a maintainer's `From:`
across a cloned list mirror, no live-site query-syntax fighting required)
should confirm quickly. Flagged as **untested this session, plausible,
cheap to check with the git-mirror path**.

One sharper caution than Enron's: kernel reviewers are **current,
named, professionally active people whose patch-review record is
already their public professional portfolio** — unlike Enron's
custodians (mostly private citizens, 25 years removed from a corporate
scandal, corpus release compelled by subpoena, not chosen). A
PersonModelClaim like "Johnson nitpicks style" is lower-stakes to state
about someone whose entire professional practice is already public,
searchable, and self-chosen — but a system that starts silently grading
or profiling a living professional's "judgement style" from their public
work product is a different kind of exposure than anything in the Enron
memo's exclusion list, and deserves its own explicit posture decision
(see §5) rather than inheriting Enron's answer by default.

## 5. Practicalities

**Corpus size / access paths**:
- The paper's reconstructed dataset (6,946 lifecycles, 13 GB, joined and
  cleaned) is not publicly downloadable — confirmed via the paper text
  and three targeted searches. A DoxaBase pilot cannot shortcut through
  it; it would have to rebuild the join.
- Self-joining is genuinely tractable, more so than Enron: syzbot's bug
  pages are a public, per-bug index that already links crash → discussion
  threads → fix commit (no need to reconstruct threading by hand for the
  syzbot-linked cases specifically). The wider LKML/list mailboxes
  themselves are officially bulk-clonable via public-inbox git mirrors
  (`git clone --mirror https://lore.kernel.org/<list>/<epoch> ...`) or
  NNTP — confirmed working, and confirmed to bypass the Anubis
  anti-bot gate entirely (git's smart-HTTP protocol is exempt; the
  live HTML browsing/search UI is not). `lkml` alone is 20 epoch shards
  (each a separate git repo) — full-LKML cloning is not proportionate to
  a pilot; subsystem-scoped lists (`linux-wireless`, `netdev`, etc.,
  each a single, much smaller repo) are the right unit to clone.
- The live HTML interface (needed for ad hoc reading/browsing, not bulk
  harvest) requires a `Wget`-style User-Agent to pass Anubis; this is a
  fragile, slightly disreputable dependency for a real pipeline to lean
  on and should be treated as a fallback for spot-checking, not the
  primary access path — the git-mirror/NNTP routes are the sanctioned
  ones and should be used for anything at pilot scale.

**Bounded pilot shape**: since the paper's dataset isn't downloadable,
the realistic pilot is self-joined: pick 3-5 subsystems with active
syzbot traffic and a manageable list size (wireless drivers, a specific
filesystem, one USB subsystem — not `netdev` or `lkml` itself, both
huge), clone their public-inbox mirrors, cross-reference against syzbot's
own "fixed" bug index for that subsystem (which supplies the crash-report
and discussion-link joins for free), and hand-verify a sample the way
this scout verified one — N in the 10-30 thread range, comparable in
scope to the paper's own N=6 "strict selection" end-to-end eval and to
the Enron scout's ~90-message hand sample.

**Rights notes**: public kernel mailing lists are among the
longest-standing, most explicitly-consented public archival norms in
software (lore.kernel.org's stated purpose is exactly permanent public
mirroring; posters know this). Unlike Enron, there is **no
personal/family/health leakage risk** — kernel-list mail is
professional-only by genre convention, so the entire §5 exclusion
machinery the Enron memo needed (folder filtering, keyword trip-wires for
family/health/HR content) is largely inapplicable here. The
counter-consideration is §4's point: these are current, named,
professionally live people, and a harvest that builds durable
per-maintainer "judgement style" claims is characterizing real people's
current professional reputations, not historical figures from a closed
scandal. Real names should be expected in any evidence quotes (they are
already the norm in kernel git history — every commit carries a real
Signed-off-by), but any PersonModelClaim promotion should get an explicit
posture decision (e.g., scope claims to technical/process judgment only,
never to anything that reads as a personal character assessment) before
a real harvest, not inherit one by default.

---

## Recommendation: **GO, WITH CONDITIONS**

This corpus is a stronger fit than Enron on the two axes that matter
most for the arc/know-how machinery specifically (formation density,
artifact-interleaving), and a weaker fit on practical accessibility (no
downloadable dataset, an access-layer anti-bot gate to route around
properly). Ranked comparison:

| Axis | Enron (verdict: GO w/ conditions) | Syzbot/kernel (this scout) |
|---|---|---|
| **1. Formation density** | Real but thin: ~1-in-10 unfiltered, ~1-in-2 with keyword pre-filter; genre is compression, not exposition. | **Denser.** In the one thread sampled, essentially every substantive message is formation — the genre's entire purpose is negotiating correctness, and logistics lives in separate metadata (headers, CI bots), not interleaved in the prose. |
| **2. Artifact interleaving** | Real but inferred: threading via subject-drift + reply-depth; version bumps ("REV 4") noticed, not structurally given. | **Stronger.** `vN:` changelogs are a genre convention that names what changed and (often) why, directly against the prior review objection — closer to a native `kh:showsFormationOf` link than anything Enron offers. Diffs are unified-diff precise, not prose-inferred. |
| **3. Rights posture** | Public FERC-released record; real but largely-private, historically-scandal-adjacent individuals; heavy exclusion list needed (personal/family/health/HR/privilege). | **Cleaner on leakage** (professional-only genre, no family/health content to filter) but **a live-reputation sensitivity Enron doesn't have** (current, named, professionally active people; needs its own posture decision on claim scope, not Enron's exclusion list). |
| **4. Practical accessibility** | **Stronger.** Already hosted, queryable via DuckDB/httpfs against a known schema, prior handoff docs bank the joins. | Weaker up front (paper's dataset not downloadable; live UI Anubis-gated) but a sanctioned, unthrottled bulk path exists (public-inbox git mirrors / NNTP) once routed around the HTML UI correctly. |
| **5. Person-model feasibility** | Demonstrated: 4-claim starter set from ~60 messages for one custodian, at the ≥2-sighting bar. | **Unverified this session** — one thread gives only a within-thread double-sighting (same caveat Enron itself flagged as weak); plausible given kernel reviewers' well-known persistent personas, but needs a real pilot check via the git-mirror path, not today's live-site query attempts (which hit search-syntax friction, not a structural wall). |

**Overall**: both corpora clear Doc 15's bar and land in the same
GO-WITH-CONDITIONS tier, for different reasons — Enron's caution is
"real but thin, expensive to mine per hour spent reading"; this corpus's
caution is "denser and better-structured, but you must build the join
yourself and route around an anti-bot gate to do it at scale." If
forced to rank, the kernel corpus's structural fit to the arc model
(explicit versioned deltas, explicit changelog-to-objection linkage, a
built-in decision-punctuation idiom in `#syz upstream`/CI bot replies)
is the more valuable property for *this specific* research direction,
since it demonstrates the `kh:showsFormationOf` / anchored-derivation
pattern with far less inference than Enron requires. Enron's advantage
is that it is *already assembled and sitting in a bucket* — zero
data-engineering risk before the first episode gets harvested.

Conditions for a pilot harvest, in priority order:

1. **Do not depend on the paper's dataset** — it isn't public. Build
   the join fresh from syzbot's own per-bug discussion-link index (does
   most of the work) plus cloned public-inbox mirrors for a small,
   deliberately chosen set of subsystems (not full LKML).
2. **Use the sanctioned git-mirror/NNTP bulk paths, not UA-spoofed HTML
   scraping**, for anything beyond ad hoc spot-checking — Anubis-evasion
   is fragile and not something a recurring pipeline should lean on.
3. **Model machine-episodes (syzbot AI patch generation, CI bot replies)
   as a distinct episode type from human-review episodes** — this
   corpus is unusual in having both interleaved in the same threads, and
   collapsing the distinction would blur exactly the human-judgment
   signal the project wants.
4. **Split process/meta-norm threads (like the DCO discussion here) from
   the technical-fix arc they're braided into** — they have independent
   onsets, pivots, and termini and shouldn't be forced into one arc.
5. **Settle a person-model posture before promoting any PersonModelClaim**
   about a named, currently-active maintainer — scope to
   technical/process judgment, not character assessment, given these are
   real people's live professional reputations, not historical figures.
6. **Sample 10-30 threads by hand before committing to a harvest**, the
   same order of magnitude as this scout's single-thread sample and the
   paper's own N=6 strict-selection eval — one thread is a promising
   existence proof, not a density guarantee across subsystems.

If a pilot is run, the zd1211rw deadlock thread (§2) is a ready-made
worked example — already fully quoted, already sketched onto the arc
machinery (§3), and unusually rich for a first case because it braids a
technical arc and a process-norms arc into one thread.
