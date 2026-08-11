# Syzbot Thread-Sampling Memo — Bounded Density Check for a Pilot Harvest

**Scope**: per the scout memo's conditions (`/home/codex/doxabase-private/knowhow-review/syzbot-scout-memo.md`),
sample 10-15+ recent syzbot bug-fix lifecycles with real discussion, grade
each A/B/C against the ARCS-1 arc criteria
(`docs/journal/knowhow-study/ARCS-1-report.md`), and recommend whether
density supports a pilot harvest.

**Access method**: sanctioned paths only. (1) `syzkaller.appspot.com`'s
public `/upstream/fixed` listing and per-bug `/bug?extid=...` pages,
fetched with a `Wget/1.21.3` User-Agent at a gentle pace (~1.2s between
requests). (2) `lore.kernel.org`'s `t.mbox.gz` per-thread mbox download
endpoint (a data endpoint, not the Anubis-gated interactive HTML/search
UI), same UA, same pacing. No public-inbox `git clone` was used this
session — judged unnecessary once the mbox-per-thread endpoint proved
cheap and precise for grading specific known threads; this is a
documented judgment call, not a discovery that cloning doesn't work.

**Network operations ledger** (all logged, well under the 60-op budget):
1 connectivity probe + 1 full fixed-bugs listing fetch + 22 bug-page
fetches + 27 thread-mbox fetches (26 in the main batch + 1 follow-up on
`cec` v2) = **52 total operations**. Zero fetches hit any anti-bot
challenge — both `syzkaller.appspot.com` and `lore.kernel.org`'s
`t.mbox.gz` endpoint returned clean content on every request, unlike the
scout's experience with lore's *interactive* HTML UI. This is a positive
operational finding for a real pilot: the sanctioned bulk-data endpoints
(bug pages + `t.mbox.gz`) need no UA workaround at all.

**Sampling procedure**: fetched the entire `/upstream/fixed` listing in
one request (5,970 bugs, all rows present server-side, no pagination),
parsed offline, and ranked by "days since last observed crash" as a
zero-cost recency proxy for "fixed recently" (a bug that's still in the
fixed list but hasn't crashed in N days was very likely fixed roughly N
days ago — confirmed against several bug pages' actual fix dates, all
landing within the intended ~6-month window; one exception noted below).
Selected 22 candidates from the top of that ranking, deliberately spread
across subsystems (wireless, usb, net, kvm, media, mm, bluetooth, bridge,
mtd, keyrings/lsm, netfs, sound/sched) rather than concentrated in one or
two lists, to avoid subsystem-selection bias in the density read.

## Screening: skip rate

Of 22 candidates screened via their bug page's "Discussions" table:

| Outcome | Count | Bugs |
|---|---|---|
| Excluded — proxy misfire | 1 | `fa6f2ee9` (mm, `folio_flags`): recency proxy pointed at a bug whose only discussion is from 2023; last-crash-days doesn't always mean recently-fixed. Not counted as a skip; just a bad pick, worth noting as a limit of the cheap proxy. |
| **Skip — single-message, auto-applied** | **3** | `b6ce23950f` (wireless, confirmed by content read: one message, zero replies, applied as-is); `95096af594` (kernel/rseq: no discussion thread at all in the bug page's index — the fix apparently landed with zero mailing-list interaction visible to syzbot's own linkage); `e9a1f5e196` (media/dvb-core: single PATCH message, zero replies — inferred from metadata, not independently content-read, to conserve budget). |
| **Discussed — graded** | **18** | see table below |

**Skip rate = 3/21 valid candidates ≈ 14%** (excluding the one proxy
misfire from the denominator). This is the density statistic the task
asked for: roughly 1 in 7 "recently fixed, has *a* linked thread" bugs
turns out to be a bot-report-then-single-patch-then-silence lifecycle
with no real review content.

## Grade table (18 discussed lifecycles)

Grades: **A** = multi-revision, reviewer objections visibly driving
deltas (`showsFormationOf` gold). **B** = one objection-revision pair or
substantive diagnosis discussion without a resulting delta. **C** =
logistics-only or bot-only (Acks, CI results, backport/tooling talk, no
technical objection).

| Grade | Bug (subsystem) | extid | Revisions | Human/machine mix | Terminus signature | Msgs |
|---|---|---|---|---|---|---|
| A | zd1211rw deadlock (wireless) | `0ec3d1a6cf` | RFC→v1→v2 (3 stages, 2 lore-visible) | AI-authored (`Assisted-by: Gemini`) draft, 2 human reviewers, `syzbot ci` bot | Silence after DCO resolution; dashboard shows merge, no on-list "applied" | 6 |
| A | vsock/virtio msg_iter (kvm/net/virt) | `28e5f3d207` | v1→v2 (2 stages) | 2 humans (author + Stefano Garzarella) + Sashiko-bot + Jens Axboe | patchwork-bot "applied, thanks!" | 12 |
| A | cfg80211 IE validate (wireless) | `cc867e537e` | v1(4msg)→v2(4msg)→maintainer override, no v3 | 3 humans (author, Johannes Berg, Jeff Johnson) | Maintainer explicitly closes it: "I applied a modified v2... not going to take v3" | 8 |
| A | dummy_hcd fifo_req UAF (usb) | `faf3a6cf57` | v1→v2 (2 stages) | 2 humans (author, Alan Stern) | Reviewed-by given on v2; silence | 7 |
| A | netfs writeback ENOMEM (fs) | `0da43efa72` | v1→v2→(Howells posts his own competing commit in-thread) | 4 humans (author, Hellwig, Howells, Wilcox) | Open at capture — Howells's alternative fix was still being negotiated; genuinely mid-arc | 11 |
| A | bridge mcast lockdep (net) | `d7b7f1412c` | v1(net)→v2(net)→v3(net-next), 3 stages | 3 humans + 1 AI-forwarded review (Simon Horman relaying an AI reviewer) | v3 not fully captured; net+net-next both show real deltas | 6 (v1+v2 only) |
| A | hsr memory leak (net) | `456957213f` | v1→v2 (2 stages) | 3 humans + Sashiko-bot | patchwork-bot "applied, thanks!" | 10 |
| A | kvm vcpu_run WARN (kvm) | `dd769db186` | v1→v2→v3 (3 stages) | AI-authored (`From: syzbot`) v1/v2 + human debugger credited (`Debugged-by:`), Sean Christopherson (human) authors v3, Sashiko-bot, Aleksandr Nogikh | "Applied to kvm-x86 misc, thanks!" — explicit maintainer close | 13 |
| A | cec delayed-work race (media) | `051024d603` | v1→v2 (2 stages) | 2 humans (author, Hillf Danton) | v2 posted, no further reply; `Suggested-by:` tag makes attribution explicit | 4 |
| B | udp_tunnel leak (net) | `eca845fb8c` | 1 (merged as posted) | 2 humans | patchwork-bot "applied, thanks!"; reviewer's design question ("could we remove RTNL long-term?") deferred, not resolved | 3 |
| B | ipv6 rcu alloc flags (net) | `84d4a405ed` | 1 | 2 humans | patchwork-bot applied; substantive but non-blocking technical explanation | 3 |
| B | userfaultfd uffd-wp (mm) | `18d274a59b` | 1 (patch possibly dropped) | 3 humans (author, Andrew Morton, Mike Rapoport) | Unusual: reviewer later asks to **drop** the patch — an orthogonal upstream change made it moot. No merge confirmed in-thread. | 4 |
| B | vlan/ethtool nested notifier (net) | `9bb8bd77f3` | 1 (4-patch series, single shot) | 5 humans (Kicinski + 4 reviewers) | All Reviewed-by/Acked-by; one reviewer says "I was drafting almost the same change" (independent convergence, not objection-revision) | 15 |
| C | sched/fair dup-fix (kernel) | `484ec80b3f` | 0 (fixed by a pre-existing, unrelated commit) | 2 humans, coincidental | `#syz fix:` bot-command syntax correction only | 3 |
| C | Bluetooth L2CAP UAF (bluetooth) | `9c40ad7c6e` | 0 (2-patch series, single shot) | CI bots only (`bluez.test.bot`, `patchwork-bot`); 2 CI test failures never discussed by a human | patchwork-bot applied despite unaddressed CI failures | 4 |
| C | ueagle-atm probe/disconnect (usb) | `e62a973f83` | 0 | 1 human, one-line Ack | patchwork-bot applied | 3 |
| C | mtd double-free (mtd) | `e9c76b56dc` | 0 | 1 human, "Applied to mtd/fixes, thanks!" (b4-ty template) | Maintainer apply-notice, no technical content | 2 |
| C | fscrypt mk_users keyring (fs/keyrings) | `f55b043dac` | 0 | 3 humans; discussion is entirely stable-backport/tooling (`b4 shazam`) logistics | No blocking technical objection; "couldn't find any obvious problem" | 5 |

**A = 9, B = 4, C = 5. A+B = 13/18 = 72% of discussed bugs.**

## Machine-episodes, noted distinctly

This corpus has *more* machine-episode texture than the scout's single
worked example surfaced. Six distinct bot/AI actor types appeared, and
critically, several are **content-generating reviewers**, not just
logistics bots — human reviewers sometimes adopt their findings verbatim
into revision changelogs:

1. **syzbot's own AI patch-generation pipeline** — drafts posted `From:
   syzbot`, tagged `Assisted-by: Gemini:...`, promoted to a human
   Signed-off-by after human review (`zd1211rw`, `kvm vcpu_run` v1/v2).
2. **`syzbot ci`** — automated pre-merge test runner ("found no issues").
3. **Sashiko AI code-review bot** (`sashiko-bot@kernel.org`, findings at
   `sashiko.dev`) — posts structured, severity-graded review comments on
   *both* AI-authored and human-authored patches. Outcomes varied by
   case: **dismissed** ("Hmm, no, that looks weird... please ignore" —
   Aleksandr Nogikh on `kvm` v2), **adopted and cited by name** ("I think
   Sashiko was right, I will send a V2 incorporating their feedback" —
   Eric Dumazet on `hsr`; "Exempt Xen. `[Sashiko]`" — Sean
   Christopherson's `kvm` v3 changelog, citing the bot in the *same*
   citation convention used for human reviewers), and **relayed by a
   human vouching for it** ("This is an AI-generated review... the human
   sending this email has considered the AI review valid, or at least
   plausible" — Simon Horman on `bridge`).
4. **`patchwork-bot+<subsystem>@kernel.org`** — pure merge-confirmation
   logistics ("applied... you are awesome, thank you!"), one per
   patchwork-integrated list (netdev, bluetooth).
5. **`bluez.test.bot`** — CI suite results; notably, two test failures
   it reported were never discussed by a human before merge.
6. **`b4-ty` auto-generated maintainer replies** — templated "Applied to
   X, thanks!" (mtd, cec) — technically human-triggered, bot-formatted.

Recommendation for a pilot (reinforcing the scout memo's condition 3):
model these as a **distinct episode type from human-review episodes**,
but *also* track the adopted/dismissed/relayed outcome as a property —
that three-way split (adopted-and-cited, dismissed, human-vouched-for) is
itself a formation-relevant signal this session did not expect to find
this cleanly.

## ARCS-1 terminus signature: holds, with a subsystem-dependent refinement

The scout's prediction — "thread silence + external merge confirmation,
no on-list narration" — **reproduces exactly** for the wireless/kvm-x86
style cases (`zd1211rw`, `kvm vcpu_run`: dashboard/tree confirms merge,
no bot narrates it, or the maintainer's own one-line "Applied to X,
thanks!" substitutes for narration).

But it does **not** hold uniformly: patchwork-integrated lists (netdev,
bluetooth) have a bot (`patchwork-bot+*@kernel.org`) that **does**
narrate the merge on-list, automatically, every time, in a fixed
template. This is a refinement, not a contradiction: the terminus
*signature* (decisions stop being decisions) still holds — nobody argues
further once the bot posts — but whether that silence is *itself*
narrated or not is a property of the subsystem's tooling (patchwork vs.
direct git apply / `b4 shazam`), not of the arc. A pilot's terminus
detector should treat "patchwork-bot reply" and "silence + external
confirmation" as two surface forms of the same underlying signature, not
try to force one pattern.

One genuine surprise: `netfs` (`0da43efa72`) and `mm userfaultfd`
(`18d274a59b`) are captured **mid-arc** — the former has a maintainer
(David Howells) actively proposing a competing fix in-thread at capture
time; the latter has a reviewer asking to *drop* the patch because an
orthogonal upstream change made it moot. Neither fits the clean
"silence + confirmation" terminus. Worth flagging honestly for a pilot:
not every "fixed" bug in syzbot's list has a settled, single-threaded
resolution — some are still being renegotiated, and "fixed" per syzbot's
bisection can mean "some commit closes the crash," not "this specific
reviewed thread's patch was the one that landed."

## Best formation quotes (5, with message-ids)

1. **Root-cause redirection overriding the original fix strategy** —
   Christoph Hellwig on `netfs` v1, `<amGfmQHmZZuBkcwq@infradead.org>`:
   > "writeback must use mempools to back resources, or __GFP_NOFAIL if
   > it can't for some reason. -ENOMEM must not happen in writeback paths
   > or your toast. So please fix the cause of this error and not the
   > symptoms."

   → v2 changelog, `<20260724073044.3400217-1-yun.zhou@windriver.com>`:
   "Dropped the writeback_iter drain loop approach (v1) per review
   feedback from Christoph Hellwig and David Howells... Instead, fix the
   root cause: use __GFP_NOFAIL..."

2. **An AI reviewer's finding adopted and named exactly like a human
   reviewer's** — Sean Christopherson, `kvm` v3 cover letter,
   `<20260724173425.278753-1-seanjc@google.com>`:
   > "v3: - Add a helper to weed out the problematic cases. - WARN in the
   > "else" path... - Exempt Xen. [Sashiko]"

3. **A human explicitly crediting a bot's review as correct** — Eric
   Dumazet on `hsr` v1, `<CANn89iKHQWQxiwCiSZGHyos5c15et60rQwX8rW1RqpPaY2ykZg@mail.gmail.com>`:
   > "In any case, I think Sashiko was right, I will send a V2
   > incorporating their feedback."

4. **Engaged curiosity as its own formation signal, then precise,
   itemized correction** — Alan Stern on `dummy_hcd` v1,
   `<c7de3923-1f68-46f9-986e-33899dce112c@rowland.harvard.edu>`:
   > "Wow! I'm impressed. How did you figure this out?" ... "Don't set
   > the new flag here... Set it here instead, so the flag is set during
   > the enti[re lifetime]"

   → v2 changelog, `<5db8bba5b3499a86cd2e776f9918126b68b2508b.1784198306.git.wangjinchao600@gmail.com>`:
   "Changes in v2 (per Alan Stern's review of v1 [1]): - Move
   dummy_giveback() above the... comment... - Set fifo_req_busy in
   dummy_queue()..."

5. **Maintainer closing a loop unilaterally, overriding the author's own
   plan** — Johannes Berg on `cfg80211`,
   `<5b4bd5885d0ea2d2f63e504180694dc37f06a3d6.camel@sipsolutions.net>`:
   > "I applied (a modified version of) v2 yesterday, so I'm not going to
   > take v3 - and anyway the bigger cleanup isn't great for wireless as
   > a fix right now. We can revisit this in wireless-next."

## Stats summary

- Candidates screened: 22 (1 excluded as a proxy misfire)
- Skip rate (single-message, auto-applied): 3/21 ≈ **14%**
- Discussed and graded: 18
- **A = 9 (50%), B = 4 (22%), C = 5 (28%)**
- **A+B = 72% of discussed bugs** — well above the ≥30% pilot bar
- Median thread length (all-versions message count per lifecycle):
  **~5.5 messages** (range 2–15)
- Zero network operations hit an anti-bot gate; 52/60 of budget used

## Verdict: density is sufficient — GO for a pilot

72% A+B against a 30% bar is not a marginal call. Three caveats keep this
honest rather than triumphant:

1. **Sample is metadata-screened, not fully blind.** The recency proxy
   and the "has a PATCH-titled discussion row" filter both bias toward
   bugs that got *some* attention. The 14% skip rate is the honest
   read of "how often does a linked-thread bug turn out to be a
   non-event" — it is not the same as "72% of ALL fixed syzbot bugs are
   A/B," which would require sampling bugs with zero linked discussion
   too (definitionally impossible to grade, but worth stating as a
   ceiling qualifier).
2. **The mechanical proxy for A is remarkably clean but small-N.** Every
   single bug in this sample with **≥2 distinct `[PATCH...]`-titled rows**
   in its bug page's Discussions table graded A (8/8). That is a strong,
   free (already-fetched-metadata), zero-content-read predictor — but
   N=8 is small; a pilot should treat it as a strong prior, not a proven
   law.
3. **A few A-grade cases are honestly mid-arc or ambiguous** (`netfs`,
   `mm userfaultfd`) — not every "A" resolves as cleanly as the
   zd1211rw exemplar. This matches ARCS-1's own honest-limits section
   ("one arc mid-flight at corpus close") — it is expected, not a flaw.

### Recommended pilot thread-selection filter (mechanical, cheap)

Two tiers, both computable from data already free once a bug page is
fetched (no additional thread-content read needed for Tier 1):

- **Tier 1 (high-precision A-predictor, zero content read)**: bug page's
  Discussions table has **≥2 rows with a `[PATCH...]`-prefixed title**
  (distinct patch-version threads). Auto-flag as a likely-A candidate;
  verify cheaply by reading only the vN changelog plus the single
  preceding objection it cites, not the full thread.
- **Tier 2 (needs a content read to separate B from C)**: exactly one
  `[PATCH...]` thread with **total message count ≥ 3** (i.e., at least
  one reply beyond the post). This tier mixes real B-grade diagnosis
  discussion with C-grade logistics/backport chatter (`fscrypt` had 5
  messages and graded C) — no free metadata shortcut found this session
  for this split; budget for reading it.
- **Skip immediately**: bugs whose only `[PATCH...]` row shows a reply
  count that equals zero beyond the post (i.e., `1 (1)` with last-reply
  date == post date) or whose Discussions table has no `[PATCH...]` row
  at all — these are the confirmed single-message/no-thread skips.

### Pilot shape estimate

- **N**: 40–60 graded lifecycles (2–3× this scout's sample), which at
  this session's ~14% skip rate and ~82% (18/22) "worth grading" rate
  implies screening roughly **55–75 bug pages** to reach that N.
- **Subsystems**: do *not* concentrate on one or two lists. This
  session's diversity (wireless, usb, net, kvm, media, mm, bluetooth,
  bridge, mtd, keyrings/lsm, netfs) is itself evidence that dense
  formation is a fairly general property of human-reviewed kernel
  patches, not a wireless-specific artifact of unusually engaged
  reviewers (Johannes Berg, Jeff Johnson). Recommend 6–10 subsystems:
  net, wireless, usb, mm, kvm, bluetooth, netfs/fs, mtd, media,
  keyrings — same set sampled here, since it already produced a clean
  read.
- **Expected yield**: at 72% A+B among discussed, 40–60 graded
  lifecycles should yield roughly **30–43 A/B episodes** — a healthy
  harvest base, comparable in order of magnitude to the paper's own N=6
  "strict selection" eval and larger than the Enron scout's ~90-message
  hand sample in episode-count terms.
- **Operation budget**: at ~1 op per bug-page screen + ~1.3–1.5 ops per
  graded lifecycle (accounting for multi-version bugs needing 2–3 thread
  fetches), a pilot of this shape is roughly 55–75 + 55–90 ≈ **110–165
  network operations** — modest, entirely on sanctioned data endpoints,
  no Anubis-workaround dependency observed necessary anywhere this
  session.
