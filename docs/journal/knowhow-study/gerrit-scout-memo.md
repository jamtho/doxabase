# GERRIT-SCOUT-1 — OpenStack Gerrit as the phase-2 harvest arm

**Date**: 2026-08-13. **Role**: reconnaissance scout, read-only, per the cross-corpus
synthesis's phase-2 recommendation (`docs/journal/knowhow-study/CROSS-CORPUS-SYNTHESIS.md`
§5.2: "GERRIT AT SCALE as the phase-2 harvest... artifact-interleaved at patchset
granularity... machine-reviewer-rich... ready-made research corpora to de-risk the
join... big enough to stress the refined filters and the shape-dialect design at N in
the hundreds"). Grading scheme and economics baseline from `SYZBOT-PILOT-1.md` and
`syzbot-sample-memo.md`. Working dir:
`/tmp/claude-1001/-workspaces-doxybase/777df466-c845-4f2c-947c-594c36cecf73/scratchpad/gerrit-scout/`.

**Access method**: `review.opendev.org`'s public REST API (`/changes/...`, no auth), UA
`doxabase-knowhow-gerrit-scout/0.1`, paced at 1.2s between requests (robots.txt asks
2s for generic crawlers — noted as a pilot correction, see Friction). **29 of 60
sanctioned-endpoint operations used, zero errors, zero anti-bot friction of any kind**
(no Anubis-style gate exists on this host at all — it is a plain REST API, not an
interactive UI). A further 9 general WebSearch/WebFetch calls were used for the
ready-made-corpora check (§3); these are outside the Gerrit-API budget and are
disclosed separately.

---

## Verdict: GO. Gerrit beats the kernel corpus on every economic axis and matches it
## on formation density, with one new, genre-specific filtering problem to design
## around before scaling.

---

## 1. API mechanics — dramatically cheaper than the kernel's mbox-per-thread route

The kernel pilot had to fetch a bug-page listing, then screen each candidate bug page
(1 op each), then fetch each thread's `t.mbox.gz` separately (often 2-3 per multi-version
bug) and parse prose diffs by hand. Gerrit's REST API collapses most of this:

- **One list call screens 50 changes for free.** `GET /changes/?q=project:X+status:merged
  &o=ALL_REVISIONS&o=MESSAGES&o=DETAILED_LABELS&n=50` returns, in a single request, every
  candidate's full patchset count, every patchset's kind (`REWORK` /
  `TRIVIAL_REBASE` / `NO_CODE_CHANGE` / `NO_CHANGE`), and every review message —
  enough to compute a density proxy with **zero marginal network cost per candidate**.
  Three such calls (nova, neutron, cinder) screened 150 merged changes and surfaced 71
  candidates meeting a `>=3 patchsets, >=5 human messages, >=2 human authors` filter —
  op 2, 3, 4 of the 29 used this session.
- **One call per change gets the full grading substrate.** `GET
  /changes/{n}/detail?o=ALL_REVISIONS&o=MESSAGES&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS
  &o=CURRENT_COMMIT` returns patchset timeline, uploader, every top-level review message
  with real names, and every label vote. **One further call**, `GET
  /changes/{n}/comments`, returns **every inline file/line comment across every
  patchset**, pre-threaded via `in_reply_to`, with an `unresolved` boolean. Two calls,
  no parsing of diffs or prose-inference of who-replied-to-whom, to reach a fully
  quotable, structurally-threaded review record.
- **Diffs are keyed and fetchable per patchset-pair, not inferred from a changelog
  paragraph.** `GET /changes/{n}/revisions/{k}/files/{path}/diff?base={k-1}` returns
  the exact code delta between any two patchsets for any file, addressed by the same
  file+line coordinates the inline comments use. Op 29 pulled this for change #994343
  and it landed exactly where the comment thread predicted (§5) — the `_is_supported_cpu_flag`
  `/proc/cpuinfo`-parsing method is deleted between ps12→ps13 and replaced by
  `_kernel_supports_amd_sev(model='sev-snp')`, the literal resolution of an inline
  disagreement about where to read CPU capability from.
- **Numeric change IDs work directly** (`/changes/994343/detail`, no need for the
  `project~branch~Change-Id` triplet), which simplified every fetch in this session.

**This is the structural answer to the kernel's changelog-fossil problem, verified,
not assumed.** In lore.kernel.org mail, a `showsFormationOf` pair is a paragraph in a
vN cover letter inferred to respond to an earlier message. In Gerrit, the objection and
the delta are both first-class, machine-addressed, and mutually locatable: the comment
carries `patch_set` + `path` + `line`; the diff between that patchset and the next is
one URL away; and a healthy fraction of threads (see grading table) resolve with an
explicit `Done` / closing reply on the SAME thread, so the pairing does not need to be
inferred at all — it is asserted by the reviewer or author themselves, in-band. Where
the kernel corpus's richest lifecycles graded down because the artifact track
*substituted* for conversation with no way to verify on a capped budget, Gerrit's
inline-comment-to-diff link is closeable in exactly one more API call, at any depth,
because the join key (file+line+patchset) is structural rather than inferred. This
directly answers the "fetch-depth-scales-with-richness" lesson from the kernel pilot:
depth here does not need to scale with guessed richness, because the two-call baseline
(detail + comments) already surfaces which threads are chained (candidates for a
follow-up diff pull) versus singleton (skip) — the richness signal and the fetch that
resolves it are decoupled from each other, unlike mbox threading where you must fetch
first to learn depth is warranted.

---

## 2. Grading: 12 changes graded across nova, neutron, cinder

Selection: from the 71 candidates surfaced by the free list-call screen, 12 were chosen
for project/subsystem/era spread (SEV-SNP security-feature series and a 2012 pre-Zuul
baseline in nova; OVN networking and RBAC validation in neutron; vendor-driver patches
in cinder, deliberately including both a thin one and a rich one to characterize the
third-party-CI-noise problem below).

| Grade | Change (project) | # | Patchsets | Chained comment threads | Terminus | Notes |
|---|---|---|---|---|---|---|
| A | libvirt: Ignore SEV-ES when SEV-SNP detected (nova) | 994343 | 18 | 12 | explicit "we agreed" close | §5 arc sketch |
| A | Add RBD XML update for migration (nova) | 974032 | 15 | 9 | IRC-referenced consensus + `Done` | bug-vs-feature-request debate resolved, then an IPv6-bracket libvirt-compat diagnosis |
| A | Fix OVN network log cross-project drop attribution (neutron) | 977349 | 18 | 14 | patchwork-style silence after 2nd reviewer's 11-comment pass | author self-narrates root-cause in patchset messages (ps4-ps9) — richer than a vN changelog |
| A | Validate RBAC `target_project` as UUID/wildcard (neutron) | 998537 | 6 | 3 | Workflow+1 after fix | clean selfCorrectionConfessed, 3rd cross-corpus sighting |
| A | Fixed compute periodic task (nova, 2012) | 6361 | 5 | 1 (formation lived in top-level messages, not inline) | maintainer approves + auto-abandon/restore cycle | hotfix-narrow-migrate-deliberately resonance (see §6) |
| A | Delegate startup instance processing to drivers (nova) | 990552 | 5 | 9 | Code-Review+2 Workflow+1, both reviewers | full expert-reframe→concession arc, quoted below |
| B | AMD SEV: omit iommu='on' for virtio devices (nova) | 909635 | 30 | 2 | quiet +2 | 30 patchsets, mostly TRIVIAL_REBASE/NO_CODE_CHANGE — patchset count is a false-rich signal here |
| B | [Hitachi] Debug instrumentation for auditing (cinder) | 979870 | 8 | 4 | +2 after explanation, not revision | reviewer objections answered by justification, not code change — diagnosis without delta |
| B | Add ASGI worker count support (neutron) | 995162 | 12 | 1 (patchset-level) | merged despite an unresolved Code-Review-2 objection | objection's resolution is off-list — a Gerrit-native changelog-fossil case, see §6 |
| C | ovn: add plain VMAC port security for VRRPv3 (neutron) | 999257 | 3 | 1 (nit only) | rubber-stamp +2s | thin |
| C | [IBM-Storwize-SVf] Invalid Exception on portset value (cinder) | 874633 | 14 | 2 | dormant 2023→2025, then merged | 169 "human" messages, ~150 of them third-party CI (see §4) |
| C | Fix temp volume project id, Tatlin storage (cinder) | 858293 | 7 | 0 | dormant 2022→2026, then merged | 21 comment threads, **zero** chained — every one a singleton vote or unreplied nit |

**A=6, B=3, C=3. A+B = 9/12 = 75%.** This is not directly comparable to the kernel's
72%/68% figures because both samples were metadata-pre-filtered (kernel: recency proxy
+ PATCH-row count; here: patchset/message-count threshold) rather than drawn from a
uniform random sample — the honest comparison is the *predictor*, not the raw
percentage (§4).

### Formation-bearing quotes (6, message-ids replaced with change#/patchset, all
### mechanically copied verbatim from the raw JSON, not retyped)

1. **Expert-reframe → concession, full arc, three participants** (#990552, nova) —
   melanie witt on ps3 (`/PATCHSET_LEVEL`): *"I think the only potential issue in this
   patch is the obvious abandonment of trying to treat these validations as
   driver-universal as though other drivers could implement vTPM or pinning. I feel
   like I would want to run this by the rest of the team for a sanity check ... make
   sure no one is strongly opposed to this idea."* → sean mooney, same thread: *"added
   gibi/sylvain becasue we were discussing the sev-snp start up checsk which to me are
   also libvirt specific and shoudl not be implmetned in the compute manger"* → Balazs
   Gibizer, ps4, `nova/compute/manager.py`: *"I'm fine with the move you proposed here.
   My only goal was not to process instances that are evacuated away from this host as
   they should not cause trouble on this host any more."* Objection, reframe-by-pulling
   in specialists, counter-proposal, concession — one thread, four days, three named
   people, structurally addressed the whole way.

2. **Evidence closing a design dispute** (#994343, nova) — sean mooney on ps11/12,
   `nova/virt/libvirt/host.py`, arguing raw `/proc/cpuinfo` reads are wrong and asking
   for hardware data (*"@gibi can you dump both form the test system you were using"*);
   Balazs Gibizer supplies it (*"Collected data from my HW [drive link]. It has new
   enough firmware that contains the CVE fix."*); Takashi Kajinami, closing: *"Thanks
   for these results. The result revealed that cpuinfo is useless in that case and the
   sysfs path is the appropriate approach. I've updated the change to use it."* and,
   on the now-resolved thread: *"I'm closing this because we agreed using sysfs path to
   determine SEV-SNP support status."* — and the ps12→ps13 diff (op 29) shows the exact
   code change this sentence describes: the `_is_supported_cpu_flag` cpuinfo-parsing
   method deleted, replaced by `_kernel_supports_amd_sev(model='sev-snp')`.

3. **selfCorrectionConfessed, third cross-corpus sighting** (#998537, neutron) — Slawek
   Kaplonski: *"correct me if I'm wrong but with this patch will will simply store all
   new RBAC entries with `target_project` converted to be valid uuid instead of just
   project id as it is in keystone. But how then validation will work..."* → Rodolfo
   Alonso: *"Good catch!\n\nThis is a mistake, I'm not sure why I changed `validate` to
   `convert_to` (I was doing some local testing). I need to revert this."* This is the
   same genre-neutral shape the synthesis found in home/email/kernel (`expertCorrectionAdopted`
   × `selfCorrectionConfessed`) — a fourth genre, unprompted.

4. **Root cause self-narrated between patchsets, no vN cover letter needed** (#977349,
   neutron) — Mohammed Naser, ps6 top-level message: *"Patchset 6: Fix
   _unset_disabled_acls clearing other logs' ACLs\n\nThe test_disable_logs failure was
   caused by two issues in the disable path:\n\n1. _unset_disabled_acls called
   _remove_acls_log(pgs, ovn_txn) WITHOUT a log_name filter. This cleared ALL ACLs in
   the SG port group, including ACLs owned by other active logs..."* — this is a
   developer's own diagnosis, addressed to future reviewers, attached to the exact
   patchset that fixes it — structurally the same object as a kernel vN changelog, but
   occurring on *every* REWORK patchset in this thread (ps4, ps5, ps6, ps8, ps9), not
   just the final one.

5. **Maintainer override + hotfix-narrow-migrate-deliberately, pre-Zuul baseline**
   (#6361, nova, 2012) — Vish Ishaya, after the author and two reviewers had converged
   on "move this to the compute manager": *"I actually think we should merge this as
   is and deal with moving it in a later patch. It isn't making it any worse than it
   already is... Just marking this +1 for now... Otherwise we can push this through and
   fix it later."* — a direct 2012 sighting of the same craft rule the kernel corpus
   twice-witnessed under `56e3c883` and `daa88ce3` (scope the fix, defer the migration
   deliberately) — now a THIRD independent corpus, fourteen years earlier.

6. **A blocking objection whose resolution is not on-list — Gerrit's own
   changelog-fossil** (#995162, neutron) — Rodolfo Alonso, Code-Review-2:
   *"Until Neutron does support other than uWSGI, this patch cannot be merged."* Adam
   Harwell replies with a substantive rebuttal the same thread. The change merges eight
   days later on other reviewers' +2s; Rodolfo's -2 vote and its resolution are never
   visible again in the record. Formation happened, but off-list (IRC, a hallway
   conversation, or simply a reviewer moving on) — the same shape as the kernel's
   off-list Sashiko URLs and the email corpus's absent contract drafts, now confirmed
   IN Gerrit too, not just in the genres that lack Gerrit's structural comment-threading.

---

## 3. Ready-made research corpora — checked, none substitutes for live harvesting

- **Review4Repair** (github.com/Review4Repair/Review4Repair): dataset for the paper
  "Code review aided automatic program repair." **Java-only**, ~15 projects (Acumos,
  Android, Unicorn, etc.) — no OpenStack, no Python. Fields (comment text, file
  before/after, patch numbers, timestamp) are exactly the shape our study wants, but
  the corpus itself is the wrong genre for OpenStack/Gerrit work; useful only as a
  format reference. Mirror hosted on Mega, current live-download status unverified.
- **CROP** (crop-repo.github.io, hosted on Zenodo): 11 systems, 50,959 code reviews,
  144,906 revisions, from **Eclipse and Couchbase only** — both Gerrit-hosted, so
  structurally the right shape (metadata CSV + discussion text + full git repos keyed
  to review IDs), but **zero OpenStack overlap**. Available and downloadable per its
  own site. Could serve as a second Gerrit-genre corpus later (an Eclipse/Couchbase
  comparison point, same role CROP plays for other studies) but does not touch the
  OpenStack scale/machine-participant properties phase 2 wants.
- **Rev-rec** (figshare, SEAA 2018, Lipcak & Rossi): 51 projects, 14 mined from Gerrit
  (~133K reviews) — built for the reviewer-recommendation task, so its record shape is
  almost certainly owner/reviewer/file/timestamp tuples for a recommendation model, not
  full comment text or diffs (unconfirmed directly — the figshare page 403'd on fetch;
  inferred from task genre and the paper's own methodology description). Whether
  OpenStack is one of the 14 Gerrit projects could not be confirmed from available
  pages this session (RevFinder, the earlier baseline it's compared against, did use
  OpenStack, but that is a different, older dataset). Even if OpenStack were included,
  this dataset's task genre makes it unsuitable to replace live harvesting for
  formation quotes.

**Verdict on this axis: none of the three ready-made corpora substitutes for live
harvesting.** Two don't touch OpenStack at all; the third is metadata-shaped even in
the best case. This *removes* one item from the phase-2 plan's de-risking list (the
synthesis proposed these as a way to "de-risk the join" before a live harvest) — the
live-API route is not just viable but the ONLY route to the actual content. That is a
net simplification, not a setback: it means phase 2 does not need to spend effort
integrating a second data format before harvesting begins.

---

## 4. The new filtering problem this scout found: third-party CI noise inflates
## message/patchset counts without inflating formation

The kernel's Tier-1 predictor (`>=2 [PATCH...]-titled rows`, zero content read) worked
because lore.kernel.org threads are compact and every message is either a human or one
of a handful of well-tagged bots. OpenStack's driver-heavy projects (cinder above all,
but also neutron's ml2 backend ecosystem and any vendor-hardware subsystem) run a
**third-party CI fleet an order of magnitude larger than the kernel's**: this session's
12-change sample alone surfaced named systems from HPE (3 product lines), Nexenta,
Fujitsu, Pure Storage, Open-E, StorPool, Fungible, Dell EMC (5 product lines), IBM
PowerKVM, NetApp, Cisco, Hitachi (2 systems), YADRO, Infinidat, VMware/VMstore,
ExaScaler, Zadara — and, critically, **these post via Gerrit's `tag=null` (i.e.
"human-authored") message channel**, unlike Zuul's own core CI messages which carry an
`autogenerated:zuul:*` tag. A naive "`tag=null` message count" filter (the direct
Gerrit analog of the kernel's PATCH-row count) is *fooled* by this: change #874633
(14 patchsets, 169 tag-null messages) and #858293 (7 patchsets, 119 tag-null messages)
both graded **C** — years of vendor-CI churn around a near-trivial fix, essentially zero
real review.

**The refined, cheap predictor found this session: count of *chained* inline comment
threads (>=2 entries under one root) from the single `/comments` call, not raw message
or patchset count.** Every A/B change in the 12-sample had >=2 chained threads; every C
had <=2 (874633 had 2 but both were single-line style nits; 858293 and 999257 had
0-1). Third-party CI bots essentially never leave inline file/line comments — they only
post top-level build-result messages — so this predictor is naturally immune to the
noise that defeats a message-count filter, and it costs exactly the one `/comments`
call this scout was already fetching per candidate. Patchset *kind* (REWORK vs
TRIVIAL_REBASE/NO_CODE_CHANGE) is the second necessary refinement: #909635's 30
patchsets are mostly rebases sitting dormant across 2+ years, not 30 rounds of review —
a raw patchset-count filter overweights it badly.

Recommended Tier-1 rule for a pilot: from the single bulk list call (already free),
compute `count(REWORK-kind patchsets) >= 3`; from one `/comments` call per surviving
candidate (still cheap — see §7 budget), compute `count(threads with >=2 entries) >= 2`.
This is a two-call, not two-tier, filter, and it is cheaper in ops-per-candidate than
the kernel's Tier-2 (which required a full content read to separate B from C).

---

## 5. Arc + machine-participant sketch — change #994343 (nova, libvirt SEV-ES/SEV-SNP)

**Onset**: Takashi Kajinami opens ps1 with a refactor to stop treating SEV-ES as
available once SEV-SNP is detected (they are mutually exclusive on real hardware but
the code checked them independently).

**Formation interior** (18 patchsets over 24 days): Balazs Gibizer's early passes are
style/testing (mock fixture usage, log level, release notes — all closed same-thread
with `Done`). The real formation is the ps11→ps12 arc: sean mooney objects that reading
raw `/proc/cpuinfo` is architecturally wrong ("we use libvirt ot get the cpu flags so
you shoudl not be emulating /proc/cpuinfo"); Takashi explains he tried the libvirt
capability API and it doesn't expose SEV/SEV-ES/SEV-SNP flags; sean mooney escalates —
not to a person above him, but to **evidence**, asking Balazs Gibizer to dump real
hardware capability output. Gibizer supplies it from his own test system. Takashi reads
the data, concludes cpuinfo is unreliable, switches to a sysfs read
(`/sys/module/kvm_amd/parameters/sev_snp`), and both reviewers independently close their
threads with near-identical language ("we agreed using sysfs path").

**Terminus**: Balazs Gibizer Code-Review+2 (ps18), sean mooney Code-Review+2 +
Workflow+1 same day — a converged, undisputed close; the pattern statement ("read
hardware capability state from the mechanism the kernel actually exposes, not from a
higher-level API that hasn't caught up yet") is exactly the shape of the kernel
corpus's kvm-asyncpf-diagnosis-to-citation arc (embodiment measured in review rounds,
not in understanding depth) — a fifth genre instance of that pattern, unprompted.

**Machine-participant layer, this one change**:
- **Zuul** — `Verified` label voter, silent infrastructure (test pass/fail gate, no
  content).
- **Quobyte CI** — a single third-party vendor CI, posting build pass/fail on every
  patchset (18 of them) with zero content beyond a log link — pure logistics, the
  OpenStack analog of the kernel's `patchwork-bot` merge-confirmation role but firing
  on *every* patchset rather than only at merge.
- **No AI-authored or AI-review-bot participant appears in this change** — a genuine
  contrast with the kernel corpus's Sashiko/Gemini-authored-patch texture from the same
  calendar period (2026). Whether this reflects OpenStack Gerrit lagging kernel-list
  AI-review adoption, or is an artifact of this 12-change, 3-project sample, is
  unresolved and should be a specific pilot question, not assumed either way.

---

## 6. Person-model density and rights posture

**Density**: real, named, cross-referenceable reviewer identities recur densely within
a project — sean mooney, Balazs Gibizer, melanie witt, and Takashi Kajinami appear
across 4 of the 6 nova changes graded this session, and Gerrit exposes (via
`o=DETAILED_ACCOUNTS`, already used) real names and emails on every message and vote,
plus a directly queryable `reviewer:<email>` search operator that would return a named
person's entire cross-project review history in one call. This is structurally a much
easier person-density corpus to build than kernel mail (no per-person query primitive
there) — **but the study's existing discipline applies unchanged**: no
`kh:PersonModelClaim` without a consent basis, and OpenStack contributors have not
consented to research modelling any more than kernel maintainers have. The kernel
corpus's "living-maintainers posture is deliberately unset" applies identically here;
this scout used role-based prose throughout (§2 quotes are attributed by name only
because the episodes are meaningless without the name, per the syzbot pilot's own
precedent, not as a person-model claim).

**Rights posture**: `review.opendev.org` is a plain, unauthenticated public REST API
(confirmed this session — no login wall, no rate-limit response encountered, `robots.txt`
only asks a 2s crawl-delay of generic crawlers). OpenStack requires contributors to
sign an Individual Contributor License Agreement covering *code* contributions; no
separate license was found governing reuse of the review *discussion* text itself —
same posture as the kernel mailing list (public archive, real professional identities,
no formal reuse license, no research-use consent). Treat identically: same unset
posture, same role-based-prose discipline, until the owner sets one.

---

## 7. Pilot shape recommendation

**N**: 150-200 graded lifecycles (3-4x this scout's N=12, comparable in scale-up ratio
to the kernel pilot's 2-3x-the-scout's-sample rule) — Gerrit's near-zero screening cost
means this is a *cheaper* target than the equivalent kernel N, not a harder one.

**Projects**: 8-10, deliberately spanning two structurally different project types
identified this session:
- **Core-service projects** (low third-party-CI noise, richest human-only formation):
  nova, neutron, keystone, cinder-core (non-driver paths), oslo.* libraries.
- **Driver-heavy projects** (high third-party-CI noise, needs the chained-thread
  filter from §4 to separate signal from vendor-CI churn): cinder (drivers/),
  neutron's ml2 backend tree, ironic.
Both types should be represented, not avoided — the noise pattern itself is a
pilot-worthy finding (a Gerrit-specific machine-participant texture: dozens of
single-purpose CI accounts per hardware vendor, distinct from Zuul's core-gate role),
and a pilot drawn only from core-service projects would under-represent it.

**Expected yield**: at this scout's 75% A+B rate on a metadata-pre-filtered sample (not
directly projectable to a blind sample, exactly as the kernel sample memo noted about
its own 72%), a conservative planning estimate of 50-60% A+B on a broader, less
hand-picked N of 150-200 should yield **roughly 90-120 graded A/B lifecycles** — well
above the kernel pilot's 32 A/B lifecycles (11 A + 21 B) from its N=47, at comparable or
lower op cost per graded unit (below).

**Operation budget**: from this session's measured costs —
- Screening is **effectively free**: one bulk list call covers up to 50-100 changes per
  project (Gerrit does not appear to cap `n=` sharply within reason; untested above
  n=50 this session, worth confirming at pilot scale). 8-10 projects ≈ 8-10 ops to
  screen well over 1,000 candidate changes.
- Grading is **2 ops per graded change** (`detail` + `comments`) to reach a fully
  quotable A/B/C verdict with threaded evidence — no separate diff-fetch is needed for
  grading itself, only for occasional spot-verification (as op 29 did once this
  session).
- A pilot targeting 150-200 graded changes: **8-10 screening ops + 300-400 grading ops
  ≈ 310-410 network operations total** — larger in absolute count than the kernel
  pilot's 142 (because Gerrit permits grading a much larger N for the same human-review
  effort, not because any single op is more expensive), but at **roughly 2 ops per
  graded change versus the kernel's ~3.0** (142 ops / 47 graded lifecycles this
  session's directly comparable ratio), cheaper per unit of harvested formation. A
  pilot could also be run at kernel-comparable scale (N=47-60, ~100-130 ops) if op
  parity rather than N parity is the design goal — that choice is the owner's, not a
  finding.

**A specific recommendation this scout adds beyond the mechanical numbers**: run the
Tier-1 filter (§4: REWORK-patchset count + chained-thread count) as a two-pass design —
pass 1 spends the ~10 free list-call ops to build the full candidate pool and rank by
the mechanical predictor; pass 2 spends the grading budget only on the top-ranked
slice. This is the direct Gerrit analog of the kernel pilot's Tier-1/Tier-2 split, but
because both signals here are available from calls a pilot needs anyway (no separate
"cheap metadata" versus "expensive content read" tiers — the chained-thread count comes
from the same `/comments` call used for quote extraction), it collapses the kernel's
two-tier design into a single grading pass with a pre-computed rank.

---

## 8. Axis-by-axis comparison against the kernel corpus

| Axis | Kernel (syzbot/lore) | Gerrit (OpenStack) | Verdict |
|---|---|---|---|
| Formation density | 68% A+B at N=47 (blind-ish sample) | 75% A+B at N=12 (metadata-pre-filtered, same caveat kernel's own sample had) | **Comparable**, pending a less-filtered pilot sample on both sides |
| Artifact-interleaving quality | vN changelog paragraphs infer the objection→delta link; comments live in prose, off the diff | Comments are structurally addressed to file+line+patchset; diffs are fetchable by patchset-pair at the same coordinates; a real fraction of threads self-close with `Done`, no inference needed | **Better** — the dangling-objection / changelog-fossil problem is structurally reduced, not eliminated (§2 quote 6 shows it still occurs when resolution happens off-list) |
| Machine participants | Sashiko (content-generating AI review bot), syzbot's own AI patch pipeline, patchwork-bot, CI runners — rich, AI-forward | Zuul (silent gate) + a large fleet of single-vendor third-party CI (logistics-only, not content-generating) + (in 2012 baseline) LaunchpadSync auto-abandon/restore + Software Factory CI (dependency-graph gatekeeper) — **no AI-authored or AI-review-bot participant found in this N=12 sample** | **Different, not simply richer or poorer** — Gerrit's machine layer is wider (many more distinct bot identities) but shallower in content generation per this sample; the AI-review question is open, not answered, and is a good pilot RQ |
| Person-model density | Role-based only; no per-person query primitive in mail archives | Same posture required (unset, no consent), but structurally denser: `o=DETAILED_ACCOUNTS` + `reviewer:` query give real names/emails and a queryable cross-project history for free | **Better infrastructure, same governance constraint** — density noted, no claims made, exactly as instructed |
| Rights posture | Public archive, real identities, no reuse license, no consent | Same: public API, real identities (ICLA covers code only), no reuse license, no consent | **Same** |
| Economics (ops per graded A/B unit) | ~3.0 ops/graded lifecycle (142 ops / 47 graded), ~4.4 ops per full A/B lifecycle harvest per the synthesis's own figure | ~2 ops/graded change (2 calls: detail+comments), screening effectively free | **Better** |
| Filtering | Tier-1 (PATCH-row count) clean but small-N (8/8); Tier-2 needs a full content read | A raw message/patchset-count Tier-1 is *worse* than the kernel's (third-party CI noise, §4); the refined chained-thread-count Tier-1 is comparably clean and free (comes from a call the pilot needs anyway) | **Different problem, cheaper fix once found** |
| Scale | N=61 episodes achievable pilot-scale | N in the hundreds achievable at comparable or lower op cost; 150,000+ merged changes exist across just nova/neutron/cinder's history | **Better** — this is the axis the synthesis specifically wanted Gerrit for |

---

## 9. GO / NO-GO / GO-WITH-CONDITIONS

**GO**, with two conditions carried into pilot design (not blockers, design inputs):

1. **Adopt the chained-inline-comment-thread count as the primary Tier-1 filter, not
   raw message or patchset count.** A message/patchset-count filter ported directly
   from the kernel pilot will systematically over-rank driver-heavy, third-party-CI-rich
   projects (cinder above all) and under-grade them relative to their true formation
   content — this scout's 858293 and 874633 are worked examples of exactly that trap.
2. **Treat the AI/machine-review-content question as an open pilot RQ, not an assumed
   yes.** The cross-corpus synthesis's docket item 3 (machine-participant vocabulary)
   names Gerrit as "the second corpus" for minting that vocabulary; this scout's N=12
   found zero AI-authored or AI-review-bot instances, in real tension with the kernel
   corpus's rich AI texture from the same calendar period. A pilot should deliberately
   sample toward projects/timeframes more likely to surface it (if it exists in
   OpenStack Gerrit at all) rather than assume the kernel's texture will simply
   reappear — and should report honestly if it doesn't, since "Gerrit machine
   participants are numerous but logistics-only, not content-generating" would itself
   be a real, useful finding for the vocabulary docket.

Everything else recommends proceeding at the scale the synthesis proposed: the API is
cheap, clean, and sanctioned; the ready-made corpora don't reduce the work but do
simplify the plan (no second-format integration needed); the artifact-interleaving
thesis holds and the changelog-fossil problem is structurally smaller than in mail; and
the economics beat the kernel baseline on every measured axis.
