# ENRON-PILOT-1 — first foreign-corpus person-model harvest (Kay Mann, mann-k)

**Date**: 2026-08-11. **Operator**: enron-pilot-1 archivist (Fable 5), owner-authorized under the
scout memo's six conditions (`/home/codex/doxabase-private/knowhow-review/enron-scout-memo.md`).
**Capsule**: `/home/codex/enron-knowhow/capsule.sqlite` — CORPUS-SEPARATE by design; nothing here
writes back to the knowhow-study capsule. **Bridge**: copy of the AIS-study bridge.py; wheel
doxabase-0.2.0 in a fresh venv.
**Close state**: validate_graph scope=all CONFORMS (0 results); staged debt 0 (one failed staged
row closed `superseded` with rationale kept); 41 observations, 36 kh:Episode nodes, 1 kh:Arc,
6 kh:PersonModelClaim, 1 person node.

---

## 1. Setup and the vocabulary-import verdict

`import_bundle kind="trig"` with `spec={"path": kh-vocab-seed.trig}` worked on the FIRST call —
473 ontology + 258 shapes triples, no errors, and `validate_graph scope=all` conformed
immediately after import. All 10 kh: classes and 41 kh: properties present; the 5 OnsetShape and
12 EpisodeShape individuals arrived intact with their ≥2-citation seeAlso anchors.

**Cross-capsule vocabulary transfer verdict: clean at the syntax and gate level, honest strain at
the semantic level (see §5).** The only import-side surprise: `list_entities` with
`graph="ontology"` and type `rdfs:Class` never surfaced the kh: classes (only rc: classes),
though they are present in the graph and retrievable by rdflib and by search. Verified presence
directly instead. Friction, not blocker.

## 2. Filter and exclusion counts (conditions 2, 4, 5 — all run BEFORE harvest reads)

Pipeline (`pipeline.py`, mechanical, in order):

| stage | count |
|---|---|
| mann-k rows, 1997–2005 window | 27,978 |
| with body-level forward-wrapper marker | 15,460 (55%) |
| Mann-authored (from_name) | 17,517 |
| …with non-empty own prose after wrapper strip | 14,949 |
| removed by (subject, date, body-hash) dedup | **10,644 (71% of authored!)** |
| deduped Mann-authored | 4,305 |
| excluded: folder family (\Calendar/\Contacts/\Tasks) | 0 (all fell earlier in the funnel) |
| excluded: family/health keyword trip-wires | 132 |
| excluded: freemail-only recipients | 26 |
| excluded: family-recipient + "Michael" thread | **265** |
| excluded: personal-subject threads (spa trip) | 11 |
| excluded: privilege-marked litigation strategy | 0 |
| **harvestable** | **3,871** |
| formation-phrase triage hits | 108 |

Notes the scout predicted and the pilot confirms:
- **No \Personal folder exists for mann-k at all** — folder exclusion alone would have excluded
  nothing. The scout's §5.2 negative finding ("not reliably siloed by folder") is the whole game.
- **The biggest personal-content catch came from recipient inspection, not keywords**: a thread
  subject-named after a person routed to a school domain plus a same-surname non-Enron address
  (265 messages once the recipient pair was trip-wired). Generic Mom/Dad/medical keywords caught
  132. Lesson for the next harvest: family *names* are unknowable a priori; family *recipients*
  are mechanically discoverable from metadata without reading bodies. Log: nothing beyond
  recipients/subjects was read from any excluded message.
- **Privilege-litigation exclusion caught 0**: Mann's practice in this window is deal work, not
  litigation. Privilege boilerplate exists but never co-occurred with litigation-strategy
  vocabulary in her own prose. (One Aug-2001 motion-to-dismiss message sat at the boundary —
  procedural speculation about an intervention motion, no privilege marker, left unharvested
  anyway.)
- The forward-detector needed 7 marker patterns (Lotus "Forwarded by", Outlook "Original
  Message", nested From:/Sent by:, "X on date" attribution lines, bare date+To: blocks,
  To:…Subject: blocks) plus trailing-attribution-line trimming. The `is_forward` flag was never
  consulted — per the scout's finding it undercounts 4–5x.
- Dedup at 71% is even worse than the scout's warning implied: mann-k's mail surfaces 3–4 export
  copies (\All documents, \Discussion threads, \Sent, \'sent mail). Any sighting-count made
  without dedup would be fiction.

## 3. Episodes and the Vitro arc verdict

**36 episodes** recorded as prose observations and typed kh:Episode (staged revision batch A,
190 triples, validated then applied), each with exactly one decision, rationale only where the
record has one, `fromObservation` anchoring, evidence_sources citing corpus doc_ids. Third
parties appear only as roles ("the senior lawyer", "her assistant", "GE's negotiator", "outside
counsel") per scout §5.3. Groups: Vitro/GE arc (8), GE-standardization initiative (7), fuel-cell
contract (3), other deal formation (18).

**The Vitro arc verdict: the scout was right — it promotes honestly.** `khea:vitro-consolidation`
is a kh:Arc (dual-typed rc:Pattern) with 8 member observations. The ARCS-1 terminus signature —
*decisions stop being decisions* — reproduces exactly: after 06-26 no position is re-argued and
the thread visibly collapses into version-chasing ("I just want to make sure that the fully
executed document has been processed"; "now I'm trying to find the signed original"), with the
subject line collapsing from clause-specific names to bare "Vitro"/"Vitro Status".
- pivotQuote (verbatim-verified against doc 3.693330, whitespace-normalized): the 06-12
  double-payment safeguard sentence.
- becameAutomatic: the double-payment exposure test + the guaranty-as-post-execution-deliverable
  device, both applied without re-derivation by late June.
- onset: kh:questionArrives (the deal arrives; her first act is "Is there any reason we can't go
  with a single contract?" — need reframed as structure question).
- **A second arc was REFUSED**: the GE-standardization initiative (Nov 2000 – May 2001) has a
  clean onset and rich members but its terminus is outside the corpus (the master form still in
  progress at the edge: "How's the GE master form agreement coming along?"). becameAutomatic
  could not be honestly asserted, so it stays episodes-only. Refusal recorded in the batch-B
  revision rationale.

## 4. Person-model claims: promoted 6, refused 0, but one only survived on new evidence

Scout candidates (all four tested against my own reading, ≥2 independent-thread bar):
1. **hedge-then-ask** — CONFIRMED, promoted with 4 evidence observations across 4 threads.
2. **forward-triage** — CONFIRMED, promoted; 5 sightings across 5 threads in 2 sighting-cluster
   observations.
3. **accountability-boundary** — CONFIRMED, promoted (Tribasa "my responsibility ended when
   Tribasa IV was signed" + "I did not authorize anyone to initial any version"); kept as ONE
   claim about dated, factual boundary-stating; the scout's suggestion to split legal-vs-blame
   was not needed once the Flight-Change blame material moved to claim 4.
4. **intent-clarification-repair** — the scout flagged this as single-thread-weak, and the flag
   was correct on the scout's own evidence. It was promoted ONLY because targeted search found
   two NEW independent-thread sightings ("I hope this didn't sound flippant, cuz I didn't mean it
   that way", 2000-09; "No offense intended... I'm still learning who does what", 2000-08).
   Without those, it would have been refused.

Pilot-discovered claims (not in the scout's four):
5. **scoped-delegation** — every commissioned review carries an explicit depth cap ("Nothing
   comprehensive, just a fatal flaw analysis"; "I only want the simplest of explanations"; "A
   discussion will be all I'm looking for at this time"). 4+ sightings, 4 matters. The single
   strongest craft signal in the whole custodian.
6. **circulate-before-send** — internal circulation before external commitment with authorship
   deliberately cheapened ("I have ZERO pride in authorship"). 3 threads over 6 months.

All claims: `assessedAt 2026-08-11`, window "2000-06-02 to 2002-01-01 (deduped, forward-stripped
Mann-authored mann-k messages)", behaviour-over-window phrasing, ≥2 claimEvidence.

**Ethics posture**: one observation (fdb34f6f…) states the second-regime basis explicitly —
research-corpus basis, NOT consent basis (Mann cannot consent; FERC public record, standard
research usage, scout-memo mitigations applied). The person node carries the posture in its
comment and rdfs:seeAlso's the observation. This is doc 16 §6.3's anticipated second-regime
policy case, now instantiated.

## 5. What foreign material broke or strained in the vocabulary (the research yield)

1. **kh:EpisodeShape mostly did not transfer.** Only 5 of 36 episodes took a hasShape:
   expertCorrectionAdopted (1), selfCorrectionConfessed (2), deferralWithTrigger (2). The other
   31 are deliberately shape-less. The 12 shapes were distilled from an agent/design-history
   corpus; email deal-work produces different recurring forms the seed has no names for.
   Candidate foreign shapes sighted ≥2 this harvest (distiller docket, NOT minted — ≥2-case rule
   satisfied but minting belongs to a distiller pass, not a harvest): *scoped-delegation-request*
   (fatal-flaw cap; ≥4), *boundary-assertion* (dated accountability correction; ≥2),
   *counterparty-position-hold-with-invite* ("Your thoughts?" pattern; ≥3),
   *precedent-conformance-check* (genesis check / OBS treatment / precedent decay; ≥3).
2. **kh:decision's "exactly one" rule fit surprisingly well** — email's compression means one
   message ≈ one decision. The strain ran the other way: several Mann messages contain 3–5
   *micro*-decisions (the 11-28 assignment-clause message decides three separate things). I
   split by the dominant decision and folded the rest into the summary; a future vocabulary
   might want the distinction between a decision and a drafting-move.
3. **kh:Arc + rc:Pattern dual-typing enforced itself** — the first Batch B draft omitted the core
   Pattern contract (patternTarget/patternText/summary/rationale) and the staging gate refused
   it exactly as designed (4 MinCount violations, graph untouched). This is the VOCAB-NOTE-KH2
   design working in a foreign capsule: arcs really are Patterns, including their obligations.
4. **onsetShape transferred cleanly**: kh:questionArrives fit the Vitro onset with no strain —
   evidence the onset kinds are more corpus-general than the episode shapes.
5. **What email cannot give the vocabulary**: kh:conversionLatency (no recorded phrases about
   time-to-conviction), kh:frameAdopted (no frame-adoption confessions — email states positions,
   not ways-of-seeing), kh:correctedInFlight (corrections happen *between* messages, not within
   them — o9's one-minute self-correction is the closest and it is two messages). The scout's
   genre-gap analysis (§4: compression, not exposition) predicts all three absences exactly.
6. **becameAutomatic is assertable from email only when the thread keeps running past the
   formation** — the Vitro arc allowed it because the same thread continued into logistics. A
   corpus of shorter threads would leave arcs unterminatable. Terminus-visibility is a property
   of the *corpus*, not the understanding.

## 6. Friction

- `record_observation` rejects free `kind` values (must be claim/observation/profile/
  query_result) — the error message taught the fix in one round. Same for `search` (`query` not
  `text`) and `record_staged_revision_review_decision` (decision enum: accepted_elsewhere,
  discarded, no_effective_change, superseded; and `resolution_revision_iri` means the NEW
  decision record, not the replacement revision — two instructive errors).
- The bridge's 25 tools do not include the staged-review-decision tool; closing the failed
  Batch B row required the core API directly (`allow_mutation_target=True` after the replacement
  was applied). If foreign-corpus pilots are to be bridge-only, the bridge needs that tool.
- `list_entities` ontology-graph blindness to the imported kh: classes (§1).
- One driver-side slip, kept honest: the first observation call succeeded but my stdout parsing
  crashed, and a naive re-run would have double-recorded it — the HARVEST-5 inspection-re-run
  trap shape again, dodged this time by seeding the IRI map with the already-recorded IRI before
  resuming.
- MinIO/DuckDB path worked exactly per the enron-study cookbook; `body_top` was not trusted (the
  scout's forward-marker findings applied to `body`); local parquet snapshot of the custodian
  slice made iteration cheap. Credentials never echoed.

## Files

- `pipeline.py` + `pipeline_counts.json` — the mechanical funnel (re-runnable)
- `minio_con.py` — connection helper (env-credentialed)
- `observations.py` + `obs_iris.json` — the 40 harvest observations and their IRIs
- `stage_a.py` / `stage_b.py` + payloads — the two applied revisions (36 episodes; arc+person+claims)
- `vitro_arc_reading.txt`, `formation_hits.txt` — the reading sets (Mann-authored, post-filter only)
