# VOCAB-NOTE-V2 — The aisv: Vocabulary, Second Revision (Session 10)

Namespace unchanged: `https://ais.study/ns#` (prefix `aisv:`). v2 acts on
your round-2 review and addenda (recorded as capsule observations — IRIs
cited throughout) plus sessions 6–9 usage evidence, with the v1 evidence
discipline intact: every changed or new term is justified by ≥2 recorded
items, cited in its `rdfs:comment` and `rdfs:seeAlso`.

Staged machinery: ontology revision `f5d7e085` (applied `fc6d1b44`), map
migration `e3a48b76` (applied `43c61b65`); both validated conforming at
scope "all"; no staged rows left open. Superseded terms were retained
with rewritten comments — nothing was deleted.

Where v1 had 25 terms (7 classes, 18 properties), v2 has 34 active terms
(7 classes, 27 properties) plus 4 superseded terms kept for history.

## 1. What changed and why — your directives, applied

### 1a. Layering and naming humility (obs 14a4f98b)

You said: draft changes are not just cargo — ballast discharge/uptake
also moves draft; layer 1 computes physical facts, layer 2 draws
operationally-relevant inferences; co-presence is a physical fact, a
relationship between the people aboard is a layered claim; *"we need to
be humble when designing information systems — our users will (often)
take our words as we write them."*

v1 already had one correctly-layered pair — SilencePeriod (fact: not
received) + silenceReading (interpretation). v2 makes that the system:

| fact (layer 1) | reading (layer 2) |
|---|---|
| aisv:SilencePeriod (unchanged) | aisv:silenceReading (unchanged) |
| **aisv:DraftChangeEvent** (new; supersedes CargoOperation) | **aisv:draftChangeReading** (new; supersedes cargoDirection, same three values incl. mandatory `ambiguous_ballast`) |
| **aisv:RecurringCoPresence** (new; supersedes OperationalTie) | **aisv:coPresenceReading** (new; supersedes tieKind, same three values) |

Two supporting properties make the layer boundary load-bearing:

- **aisv:readingBasis** — every layer-2 reading states the layer-1
  evidence it rests on. This generalizes v1's hullContinuityBasis lesson
  (the 367369920 fleet clone forged its own corroborator: a basis must
  be stated, never assumed) to all readings.
- **aisv:trackContext** — your berth/anchor/underway point, using
  session 7's M8 values verbatim (`at_berth`, `at_anchor`,
  `no_dwell_nearby`, `dwell_unclassified`): M8 already operationalises
  this by joining M4 draft events to the M7 dwell layer, so the
  vocabulary now names what the method already measures.

### 1b. Candidate vs declared identity (obs 3b63b49b, 72d7a572)

You said: an AisIdentity is the product of an analysis process that
decides a pattern really looks like one transmitter — facts hang off it
— but "this definitely is hull h" is declared only against a solid
non-AIS record; AIS-only-inferred transmitters are ephemera.

- **aisv:declaredHullRecord** (new) — names the solid non-AIS record
  (flag-state / port / commercial registry) anchoring a hull
  declaration. The threshold is encoded in its semantics: **no map
  resource carries it yet, and that absence is the point** — every
  current emitter is an AIS-only candidate. Session 6 already practiced
  the restraint you asked for: EVER FOCUS's internally-consistent
  IMO/call-sign profile was *not* treated as a declared hull (a shore
  transponder reusing a real identity can't be excluded from the feed
  alone).
- **aisv:externalBasis** (new) — the weaker cousin: marks a statement as
  resting partly on non-feed knowledge, naming source and strength.
  Sessions needed this in prose twice (the COMFORT story's
  orientation-only USNS Comfort identification; the gear-buoy story's
  ITU block-convention reasoning). Only declaredHullRecord crosses the
  declaration threshold.
- aisv:Emitter is relabelled "physical emitter (AIS-inferred candidate)"
  and its comment now says the candidate/ephemera part out loud;
  AisIdentity's comment carries your addendum-2 framing.

### 1c. Indexical assessment windows (obs 8f177325)

You said: operatingProfile must track when the claim was made and in
what information context — two years of AIS now, almost 20 to add.

- **aisv:assessedAt** (new) — the analysis date (contrast
  startDate/endDate, which are event dates).
- **aisv:assessmentDataWindow** (new) — the data seen (e.g. "NOAA AIS
  feed, 2024-01-01..2025-12-31").
- operatingProfile and emitterMultiplicity comments now declare
  themselves indexical and require these companions. The migration
  back-filled both properties onto all 8 profile-bearing map resources,
  dated from the recorded history timestamps of the sessions that made
  the assessments (2026-07-06 / 2026-07-07).

### 1d. State vs ephemera (obs 72d7a572, 563873b6)

You said: predicted-transmitter sets and event populations are
regenerable run artifacts; deterministic derivation makes exposing
events of all types unproblematic. Sessions 8–9 already practice this
(populations in work/*.parquet, promoted exemplars in the graph). v2
gives the practice hooks instead of fighting it:

- **aisv:derivedFromRun** (new) — a promoted exemplar names the run
  (method + parameters/artifact/session) that produced and could
  regenerate it.
- **aisv:representsDetectorRows** (new) — states exactly which
  mechanical detector rows a resource stands for, in both mismatch
  directions: one real event split across rows (the COMFORT 68-day
  deployment M3 reports as two gaps) and one resource standing for a
  cluster (the NOR'EASTER 43- and 16+-event M4 aggregates). Both were
  couldn't-says recorded in prose by sessions 5–6.
- **aisv:ofEmitter** (new) — scopes an event/state/assessment to the
  specific physical unit it concerns when MMSI-level ofIdentity is too
  coarse; session 6 needed exactly this ("applies to the dominant
  occupant only") for the 374158000 statics correction.

## 2. What deliberately did not change

- **Voyage** — still no term. Your words: no version that works for all
  vessels in your head right now (obs 92240e42). Stays on the list.
- **RecurrentPattern / trade lanes** — you called the concept "a great
  idea" and agreed to wait for more evidence. representsDetectorRows
  covers the provenance need without nailing the concept down early.
- **GearBeacon class / gear-fleet multiplicity value** — checked against
  the ≥2-story bar and failed it honestly: the feed's 941xxxxxx buoys
  (467 of them) each broadcast under their *own* MMSI, which
  `emitterKind "gear_beacon"` already covers; your same-MMSI
  battery-in-COG fleet (obs 9333b23f) is unobserved in this feed so far.
  Your addendum is now cited in the emitterKind and emitterMultiplicity
  comments (benign M2 positives; COG plausibility screen), and the
  class waits on the couldn't-say list for an in-feed sighting.
- **IdentityChange events as primitive** — your usage-period alternative
  (obs 563873b6) is recorded in the term's comment as the isomorphic
  alternative; v2 keeps the event form because the recorded stories are
  event-shaped and the two forms are interconvertible. A UsagePeriod
  class is on the couldn't-say list for when message-to-transmitter
  matching against pre-minted sets begins.
- **datingQuality gains no `not_a_real_world_event` value** — you tied
  that to the primitive question, which is still open.
- **Place as a resource, structured draft values, dwell attribute
  pile** — all waiting on your RDF/dataframe rule of thumb
  (obs 92240e42); the M8/M9 practice of parquet populations + graph
  exemplars is the working answer meanwhile.
- All v1 value sets (dwellKind, silenceReading, changeMechanism,
  hullContinuityBasis, emitterKind, emitterMultiplicity, and the
  reading values carried over from cargoDirection/tieKind) are
  unchanged — no usage evidence demanded new values.

## 3. The couldn't-say list, v2

Carried forward or newly surfaced; each needs ≥2 more recorded items to
graduate:

1. **Observed voyages/excursions/repositionings** — unchanged from v1;
   expert confirms no universal formulation yet.
2. **Recurring event clusters / trade lanes as first-class resources**
   — the aggregation *provenance* is now stateable
   (representsDetectorRows), but the lane/cluster concept itself stays
   deferred by agreement.
3. **GearBeacon class / benign gear-fleet emitterMultiplicity value** —
   needs an in-feed same-MMSI gear fleet (M2 + battery-curve COG
   signature is the recorded probe recipe).
4. **MmsiUsagePeriod** (hull-tagged usage spans) as alternative/
   complementary identity primitive — becomes live when external
   reference sets (pre-minted transmitters) enter the study.
5. **datingQuality `not_a_real_world_event`** — tied to (4).
6. **Place as a resource / gazetteer** — awaiting the RDF-vs-dataframe
   rule of thumb; Foursquare-places join (obs 8f7db46c) may force it.
7. **Operating-tempo metrics** (km/month, duty ratio) — still prose;
   candidate rc:ObservedProfileMetric reuse.
8. **Structured draft values** — still prose bands; M8 works in
   dataframes.
9. **Tow/escort legs as events** — expert: obviously useful once
   fine-grained track analysis starts; not yet.
10. **Emitter home base** — still prose.
11. **Per-identity data-quality annotation** (Wyoming fix, GPS
    degradation) — still rc:Observation/rc:KnownCaveat territory.

Newly retired from the v1 list: merged-gap provenance (#3-adjacent, now
representsDetectorRows), per-emitter event scoping (now ofEmitter),
background-knowledge sourcing (now externalBasis), assessment windows
(now assessedAt/assessmentDataWindow).

## 4. Note on method

v2 was done through the capsule's own staged machinery: staged graph
revisions with pre-stage validation, read-only apply checks, apply, and
scope-"all" SHACL validation after each apply; the map migration
re-typed the two affected resources rather than bridging (their own
comments already described draft-inferred, asymmetry-read events — the
new terms say what they meant). Superseded terms remain in the graph
with their v1 meanings quoted verbatim inside the supersession notices,
so no reader of the ontology can mistake a superseded term for a live
one, and no history is lost.
