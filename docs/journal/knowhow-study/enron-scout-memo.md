# Enron Corpus Scout Memo — Multi-Person Know-How Source Assessment

**Date**: 2026-08-11 (scout run)
**Author**: scout sub-agent (read-only reconnaissance; no capsule writes, no harvest)
**Scope**: assess whether the Enron email corpus (s3://enron-emails, via MinIO)
can serve as source material for multi-person know-how capture per Design
Doc 15 (`doxabase_design_docs/15-know-how-generalization.md`) — episodes,
understanding-arcs (per `docs/journal/knowhow-study/ARCS-1-report.md`), and
PersonModelClaims.

**Method**: DuckDB + httpfs directly against the MinIO bucket, reusing the
schema/join knowledge already banked in `docs/journal/enron-study/`
(`enron_docs_overview.md`, `enron_analysis_views.md`, `enron_query_cookbook.md`,
`enron_starter_tasks.md`) rather than rediscovering it. Bucket layout
confirmed identical to the prior handoff: `eml_messages.parquet`,
`eml_attachments.parquet`, `xml_messages.parquet`, `xml_attachments.parquet`,
same columns, same doc_id/parent_doc_id join keys. Sampled four custodians
with dense SENT-folder mail: **kaminski-v** (Vince Kaminski, head of
research/risk management), **mann-k** (Kay Mann, contracts/deal lawyer),
**dasovich-j** (Jeff Dasovich, regulatory/government-affairs lobbyist during
the California power crisis), **lavorato-j** (John Lavorato, president of
Enron America). Read ~90 messages total across free browsing and a
formation-phrase-indicative keyword search (`"i think we should"`, `"i'm not
sure"`, `"on the other hand"`, `"we decided"`, `"i disagree"`, `"in
retrospect"`, etc. against `body`).

---

## 1. Formation vs. logistics — what the sample actually shows

**Verdict: a real but thin seam.** Most SENT-folder volume is logistics,
routing, scheduling, and pure forwarding — but scattered through it are
short, real moments of a person weighing something, and a few longer ones
that show sustained reasoning. The seam is minable but not dense: in an
unfiltered date-ordered sample, formation-bearing messages ran roughly
1-in-8 to 1-in-15; a targeted keyword pass raised the yield to roughly 1-in-2
of what it returned (see §6 for the technique). This matches the "sampling
bias" problem named in Doc 15 §2 almost exactly, except here the skew isn't
toward the human's weakness — it's toward the *medium's* weakness: email
is disproportionately used for logistics precisely because deliberation
happened on the phone or in person and only its outcome got typed.

Eight real formation-bearing passages, verbatim, with message ids:

1. **Kaminski, choosing a valuation approach, not just an answer** (deciding
   *how* to value something, and generalizing the method) —
   `doc_id=3.362853.LO0H1GQLUUQI0QAXRHNFG3JK54QHIQFRB`, 2000-01-20:
   > "We are working on the second approach to the problem: we try to come
   > up with a numerical estimate of the value of this option... The value
   > of such an option is case specific; so we shall rather produce a
   > template you can use for valuation case by case."

2. **Kaminski, declining with stated reasoning, not just a no** —
   `doc_id=3.363673.GYOAOJNPZ0IDW251LCPVZXONG05FWJCUB`, 2000-01-24:
   > "I agree with you. They do not seem to have the market penetration we
   > need. The benefits don't justify the expense."

3. **Kaminski, a personnel judgment call with an articulated principle** —
   `doc_id=3.363424.LRBFZXYONBUC2P3CTRU155GFDOZCUSWZA`, 2000-03-09:
   > "My recommendation is that we should draw a line in the sand... We
   > just need clarity and ability to plan our human resource needs... we
   > shall not hold his decision to pursue his entrepreneurial plans
   > against him."

4. **Mann, a negotiating position with the reasoning shown, then an
   explicit ask for pushback** — `doc_id=3.710743.LWYV0A5ISVJMXYXTJKY1P1JNU5AS4PQWB`,
   2000-06-12:
   > "It seems to me that the time GE has to remit the payment to ENA should
   > remain 3 days. I don't see a reason to stretch it to 7 days, since it
   > represents a double payment. Your thoughts?"

5. **Mann, flagging what she doesn't understand instead of pretending
   fluency** — `doc_id=3.710780.OSDGFJMBYR0KOR335IEFDE1MHN1Q2EFVB`, 2000-06-19:
   > "I'm not sure I understand their objection to the wording about the
   > guaranty. Do you think that there is going to be a problem with them
   > accepting the Mitsui guaranty?"

6. **Mann, a genuine micro-correction arc inside one thread** (disagreement
   → clarifying she wasn't attacking the person → coming around) —
   `doc_id=3.715780.KZZBUD1Y3KFHNHAMACWYXM12ZMM2TEEHB` and
   `doc_id=3.693031.BTXUMGD4B3QCYIGWTG1VILUW2PRC2JTPA`, 2000-08-01:
   > "I disagree. NONE of the problems I've had in the last 2 weeks can be
   > attributed to changes..." → "I wasn't blaming you. I was just
   > disagreeing with the statement that changes have caused the problem."
   > → "She may turn out to be great, just because she becomes extra
   > cautious with us."

7. **Lavorato, replacing one risk metric with another, tersely but with a
   reason** — `doc_id=3.368194.N55KOHDX5XDKU5N0ZKAPNWDCRLOOADYCA`, 2000-07-28:
   > "I asked about loss limits a couple months ago... I think we should
   > get rid of the whole concept. VAR is the relevant concept."

8. **Dasovich, withdrawing from an initiative while preserving the idea
   under it** — `doc_id=3.110192.EPSYOWVFVHPVIJU0KR0AIOIX05ZXESCLA`, 2000-09-08:
   > "I notified the group this week that Enron would not be participating...
   > From my perspective, the effort turned out to be a rather big
   > disappointment... I still think the idea of an energy summit is very
   > promising. But the forum that these folks are creating ain't the right
   > one."

None of these are deep essays — email compresses reasoning into one or two
sentences, then moves to the ask. That is itself a genre fact worth
recording (§4): **the corpus shows reasoning in outline, not in the
worked-through form a transcript or interview would give you.** The
"wrong instinct corrected" case (#6) is the strongest single find and it is
also the smallest — a half-day exchange about a flight change, not a
business decision at all. That is a caution about where the good stuff
actually lives in this corpus: interpersonal micro-repair, not boardroom
strategy.

## 2. Thread/arc feasibility

**Verdict: yes, with real work.** The Vitro/GE consolidation-agreement
negotiation (Kay Mann, June–July 2000) is a clean example of a decision
playing out across ~25 messages with a legible subject drift that itself
tracks the decision's stages:

```
Enron Monterrey/Vitro (6/2)
  -> Vitro termination agreement (6/6)
  -> Assignment of GE Contract regarding Vitro Project (6/8-9)
  -> Vitro consolidation agreement (6/12)
  -> Tax Language Changes to On/Off Shore Contracts for Vitro (6/12)
  -> Consolidation Agreement (6/13)
  -> VITRO (Monterrey) GE WRAP REV 4 (6/16)          [note: "REV 4" — revision tracking]
  -> Vitro GE consolidation Agreement comments (6/16-19)
  -> Vitro (6/20-21)
  -> Vitro Status (6/21)
  -> Vitro/Termination agreement (7/14-18)
```

Sketch of how this becomes episodes + an arc:
- **Episode 1** (6/12, doc `3.710743...`): Mann proposes holding payment
  terms at 3 days against GE's ask for 7, with reasoning ("double
  payment") and an explicit invitation for correction.
- **Episode 2** (6/19, doc `3.710780...`): Mann flags a specific clause
  she doesn't understand (guaranty wording) and asks a colleague to
  confirm whether it's a real problem or a non-issue.
- **Episode 3** (6/19, doc `3.693298...`, Barto's reply): the clause-by-clause
  GE response comes back — some edits accepted, some rejected, each with a
  stated reason (e.g., "GE does not have any defenses under either contract
  for insolvency... because they are events of breach of contract").
- **Episode 4** (6/16, "REV 4"): a revision-number bump — evidence the
  document itself is being iterated, which is exactly the kind of anchor
  an anchored-derivation / SourceSpan model (docs 13/14) would want to hang
  off a specific artifact version.
- **Arc**: "consolidation-agreement clause negotiation" — starts with an
  ambiguous clause (formation: does this matter or not?), moves through a
  clause-by-clause position exchange, and terminates not in a single
  decisive message but in the pattern ARCS-1 already found generalizes:
  the thread just stops generating new positions once term acceptance
  stabilizes (visible as the subject collapsing from clause-specific names
  back to the bare "Vitro" / "Vitro Status" check-ins). That "decisions
  stop being decisions" terminus signature from ARCS-1 §1 reproduces here
  almost exactly, in a completely different domain (contract law vs.
  product design), which is a mild point in favor of the vocabulary being
  genuinely general rather than an artifact of the design-history corpus
  it was distilled from.

Caveat carried over from the prior capsule study and reconfirmed here:
**do not thread by `message_id` alone.** The store's own dedup finding
(same message appearing under 2+ doc_ids from parallel PST exports) means
naive threading will double-count episodes unless dedup runs first (see §6).

## 3. Person-model feasibility (Kay Mann, mann-k)

Behavior patterns with ≥2 sightings, the PersonModelClaim bar:

1. **Hedge-then-ask opener**: states uncertainty, then immediately converts
   it into a concrete, answerable question rather than leaving it as a
   complaint. Sighted in the GE Letter Agreement message (#4 above), the
   Vitro consolidation-comments message (#5 above), and again in the CPCN
   Update thread (`doc_id=3.715807.O5IISFMJQU5PKQZHIVWSM0YF1IINTGMQA`,
   2000-07-25: "Is not having the CPCN an absolute bar to beginning
   construction? What are the risks?"). Three independent threads, same
   shape.

2. **Explicit action/no-action triage on forwards**: rather than a bare
   "fyi," she frequently tags forwarded material with an explicit
   relevance/action marker. Sighted in
   `doc_id=3.710797.MAMAUJKHK5HZU2EZH33O0KOPGNJ4F03AA` ("For information
   but no action on your part at this time") and
   `doc_id=3.717515.J11PQ3KE2IZIOAHJYP5ZUGGJHFBJZDKAB` ("please give it a
   look for 'fatal flaws'"). Two independent threads.

3. **Sharp, explicit boundary-drawing on personal responsibility**: states
   the edge of what she is and isn't accountable for, without softening.
   Sighted in `doc_id=3.693213.AYHMPTCLO1W5WEHSYZSL34GD51DO354EA` ("I am
   not responsible for THIS Tribasa mess. My responsibility ended when
   Tribasa IV was signed.") and echoed in tone in the Flight Change thread's
   "I wasn't blaming you. I was just disagreeing with the statement..."
   Two sightings, related but distinct triggers (a legal-liability boundary
   vs. an interpersonal-blame boundary) — worth keeping as two separate
   claims rather than merging.

4. **De-escalates friction by re-stating what she meant, not what she
   feels**: seen twice within the single Flight Change thread (quote #6)
   — a within-thread repetition, so it clears "≥2 sightings" only if a
   sighting is counted per message rather than per episode; a real
   PersonModelClaim pass should look for a second, independent thread
   before promoting this one. Flagged as the weakest of the four.

This is a workable four-claim starter set from ~60 read messages for one
custodian — comparable density to what a first archivist pass over a design
journal produces, though the claims here skew toward professional style
(how she asks, how she triages, how she draws boundaries) rather than
domain judgment (how she actually decides a contract term is acceptable).
The latter is present (§1, §2) but sparser and requires following full
threads, not single messages.

## 4. Genre gaps vs. chat/transcript sources

- **Compression, not exposition.** Reasoning arrives pre-compressed into a
  sentence or two before the ask; there is no equivalent of a transcript's
  run-on thinking-out-loud. An agent transcript shows the dead ends; these
  emails mostly show the surviving conclusion with a one-line gloss on why.
- **Authorship is frequently not the custodian's.** This is the single
  biggest structural gap and it is *quantifiable*: of Kaminski's
  body-populated SENT messages, 5,385 of 11,705 (46%) contain a
  "Forwarded by" marker in the body — but only 1,173 (10%) are flagged
  `is_forward = true`. The `is_forward` column undercounts actual
  forwarding by roughly 4-5x because it appears to key off subject-line
  "Fwd:" conventions that Lotus Notes/Outlook forwarding often doesn't
  produce. **Any harvest must detect forward-wrapper markers in the body
  text itself** ("---- Forwarded by X ----", "-----Original Message-----",
  nested "To:/cc:/Subject:" blocks) to isolate what the custodian actually
  wrote from quoted upstream authors — otherwise a PersonModelClaim risks
  attributing someone else's prose and reasoning to the wrong person. Same
  distribution roughly holds for mann-k, dasovich-j, lavorato-j (30-30-30%
  body-has-forward-marker range; see §6 counts).
- **No visible audience-adjusted register shift.** Unlike a coached
  interview, there's no elicitation — nobody is asking "why did you pick
  that." What you get is what was already going to be written anyway,
  filtered through 2000-era corporate email norms (terse, hedge-heavy,
  deniability-conscious in the regulatory/legal threads especially).
  Formation that happened by phone or in person — which the sample
  suggests was the norm for anything consequential — is invisible by
  construction, mirroring Doc 15 §2's point about the phone-call sales
  example almost exactly.
- **Threading is reconstructed, not given.** `message_id` is not a stable
  key (documented in the prior handoff and reconfirmed); arcs must be
  built from subject-line drift + reply_depth + date + custodian/folder,
  which works (§2) but is inference, not ground truth, and will
  occasionally mis-thread near-duplicate subjects.
- **Duplicate rows across parallel PST exports.** The same message
  frequently appears under 2+ `doc_id`s (visible directly in the Kaminski
  sample above — several message pairs share identical bodies, dates, and
  subjects but different doc_ids). An episode harvester needs body-hash or
  (subject, date, truncated-body) dedup before counting anything as "≥2
  sightings," or it will manufacture false replication.

## 5. Responsible-harvest exclusion list

The corpus is the FERC-released public record (long-standard in academic
NLP/network research since ~2004), but it contains real people's private
lives, swept in wholesale because whole mailboxes were subpoenaed, not
because the private content had any bearing on the investigation. A
responsible pilot harvest should exclude, at minimum:

1. **Explicitly personal/family folders.** A `\Personal` folder exists for
   many custodians (739 messages across the sampled custodians alone;
   subjects include birthdays, family health updates, travel, personal
   correspondence with named children/parents/siblings). Exclude by
   folder-family classification (`enron_analysis_views.md`'s
   `folder_family` view already isolates `calendar`/`contacts`/`meetings`;
   extend the same pattern to `personal`).
2. **Personal/family content is NOT reliably siloed by folder** — this is
   an important negative finding, not a reassurance. The sampled
   `dasovich-j` "sent" folder (not `\Personal`) directly interleaves
   business regulatory correspondence with family birthday-card logistics,
   a "Mom's retirement" cruise-planning thread, and casual messages to a
   partner. The Kay Mann "sent" sample likewise includes an unmarked
   family email discussing a parent's medical "knee incident." **Keyword/
   entity-based filtering (family first names, "Mom," "Dad," home
   addresses, medical terms) is necessary in addition to folder exclusion,
   not instead of it.**
3. **Third-party HR/personnel matters about named, non-consenting
   employees.** Sampled examples: an employee's compensation and
   poaching-risk situation discussed by name (Lavorato/Delainey thread,
   `doc_id=3.387241...`); an intern's compensation-adequacy discussion
   (Kaminski thread); a discharge-adjacent situation ("Brad will not show
   up on March 15... draw a line in the sand," #3 above) discussing a
   named individual's job status. These are legitimate know-how material
   *about the custodian's management judgment*, but the third party's
   name/identifying detail should be redacted or generalized before any
   claim references them, distinct from the custodian's own reasoning
   which is the actual asset.
4. **Attorney-client privileged material**, distinguishable from Kay
   Mann's ordinary contract-drafting reasoning (which is exactly the
   valuable know-how — how a deal lawyer reads a clause). Several sampled
   messages carry explicit privilege markers ("PRIVILEGED and
   CONFIDENTIAL," "This email message... contains confidential
   attorney-client pr[ivileged material]"). Litigation-strategy content
   specifically should be excluded even though it is technically public
   post-FERC-release; ordinary deal-negotiation reasoning is the target,
   not litigation posture.
5. **Health information of any kind**, self- or family-referenced,
   encountered incidentally (as above) rather than sought — the sample did
   not surface a dedicated health-content stream, but the interleaving
   finding in (2) means it will appear unpredictably and needs a keyword
   trip-wire, not a folder rule.
6. **Anything from custodians not selected for the pilot.** 151 distinct
   custodians exist; a pilot should scope to a small, deliberately chosen
   set (as this scout did) rather than corpus-wide ingestion, both for
   ethics (minimize exposure surface) and for cost (1.21M plausible-date
   messages total; a full-corpus harvest is not proportionate to a pilot
   question).

None of this is a blocker — it's the same shape of exclusion list any
mailbox-based corpus needs, and the two negative findings above (folder
filtering insufficient; is_forward flag insufficient) are exactly the kind
of thing a pilot is for catching before a real harvest runs.

## 6. Supporting counts (for verification)

- Bucket layout: `s3://enron-emails/{eml_messages,eml_attachments,
  xml_messages,xml_attachments}.parquet` — unchanged from the prior
  handoff's documented schema.
- 151 distinct custodians; 1,210,548 messages in the plausible 1997-2004
  date window (matches `enron_analysis_views.md` exactly).
- SENT-folder, body-populated message counts for the four sampled
  custodians: kaminski-v 11,705; dasovich-j 14,524; mann-k 9,037;
  lavorato-j 3,744.
- Forward-marker-in-body vs. `is_forward` flag (SENT, body-populated):
  kaminski-v 5,385/11,705 (46%) vs. 1,173 (10%) flagged; mann-k
  3,546/9,037 (39%) vs. 487 (5%); dasovich-j 3,447/14,524 (24%) vs. 1,073
  (7%); lavorato-j 680/3,744 (18%) vs. 147 (4%). The gap is consistent
  and large across all four — a structural property of the corpus, not
  noise from one custodian.
- Formation-phrase keyword scan (~28 phrases including "i think we
  should," "on the other hand," "i disagree," "we decided," "my
  recommendation," "in retrospect") against 40-row samples per custodian
  returned 18/40 (kaminski-v), 21/40 (mann-k), 11/40 (dasovich-j), 8/40
  (lavorato-j) unique matches after de-duplicating parallel-export
  doc_ids — a cheap, effective first-pass filter for where to spend
  reading time.
- `reply_depth` is populated and usable for thread reconstruction
  (1,025,481 rows at depth 0 down to a long tail past depth 40).
- `\Personal` folder-family volume across the four sampled custodians:
  739 messages (metadata/subject-only scan; bodies not read for this
  count beyond what was already sampled elsewhere).

---

## Recommendation: **GO, WITH CONDITIONS**

The corpus clears the bar Doc 15 sets — it shows *some* formation, not
just outcomes, and threads reconstruct into coherent arcs with real
stage-by-stage position changes (§2's Vitro arc is a genuine, checkable
example). Person-model claims are buildable at the sighting bar the
project already uses (§3). But the yield is low relative to effort: on
this sample, a naive read finds real formation in roughly 1-in-10
messages; a keyword pre-filter roughly doubles the hit rate but still
returns plenty of near-misses (routing, scheduling, one-line forwards).
This is a harder corpus than a design-history journal or a coached
transcript — it was not written to explain anyone's thinking to anyone,
which is the whole difference from the corpus the pilot in Doc 15 §4 has
already validated against.

Conditions for a pilot harvest, in priority order:

1. **Scope to a small, named custodian set** (start with the four
   sampled here, or a similarly deliberate short list) — not corpus-wide.
   Both the ethics posture (§5) and the yield economics favor depth over
   breadth.
2. **Build the body-level forward-detector before harvesting anything**
   (§4) — this is a five-minute regex/heuristic pass, and skipping it
   will attribute other people's reasoning to the wrong custodian at a
   ~30-45% error-prone rate on this evidence.
3. **Run the keyword pre-filter as a triage step**, not a hard filter —
   it roughly doubles yield but the memo's best example (#6, the Flight
   Change micro-correction) is exactly the kind of small interpersonal
   moment a keyword list might miss if tuned only toward business-decision
   language. An archivist pass still needs to read broadly, not just
   query narrowly.
4. **Apply the exclusion list in §5 before any capsule write** — folder
   exclusion plus a keyword trip-wire for family/health/HR terms, applied
   to the custodian-scoped subset from (1), not the full corpus.
5. **Dedup by (subject, date, body-hash) before counting sightings** —
   parallel PST-export duplicates are common enough (visible directly in
   the samples) to inflate PersonModelClaim evidence counts if not
   caught.
6. **Treat this as a genre complement to, not a replacement for, the
   transcript/journal harvest** already underway per Doc 15 §4 — the
   Enron corpus is likely to be better at professional-style and
   negotiating-posture claims (§3) than at deep domain-judgment arcs,
   simply because email compresses the latter away by construction (§4).

If a pilot is run, the Vitro/GE consolidation thread (§2) and the Kay
Mann custodian (§3) are ready-made starting points — already sampled,
already showing a checkable arc and a four-claim person-model seed.
