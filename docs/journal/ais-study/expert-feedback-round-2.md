# Expert channel round 2 — James's VOCAB-NOTE.md review (2026-07-07 night)

Verbatim-faithful digest of James's review of the session-5 aisv:
vocabulary design note. Source: conversation, reviewed in bursts.

## Agreements

- Hull-in-the-water vs broadcast AIS identity split: agreed, wanted.
- Capturing the dataset's flaws in the ontology semantics: "exactly what
  we need."
- Evidence-based ontology design over armchair: endorsed.
- dwellKind liked; Recurring-events concept "a great idea" — agree wait
  for more evidence before nailing down.
- Places as resources: "I dearly want to use AIS data as the source for
  making maps."

## Challenges and design guidance

1. **Alternative primitive**: his prior practice — "the vessel we
   internally tag as xyz was broadcasting under MMSI m during t1–t2"
   (hull-tagged MMSI-usage periods). Notes the isomorphism with
   IdentityChange events; different applications prefer one or the other
   as primitive; many modelling choices admit several workable forms.
   Questions whether fromIdentity/toIdentity event modelling is needed at
   all vs usage periods. (Also: "datingQuality for non-events" touches
   the same what-is-primitive question.)
2. **Deterministic derivation principle**: if events are a purely
   functional/deterministic product of input broadcasts (+ integrated
   sets), exposing events of ALL types is unproblematic — regenerable by
   classical code. Only agent-analysis products lack this property.
3. **Layered pipeline, naming humility**: draft changes are not just
   cargo — he has seen draft change from ballast water discharge/uptake.
   Keep terms close to the observed facts. His experience: layer 1
   computes physical facts; layer 2 draws operationally-relevant
   inferences from layer-1 output. Same for OperationalTie: co-presence
   is a physical fact; stating (not suggesting) a relationship between
   the people aboard needs more. **"We need to be humble when designing
   information systems — our users will (often) take our words as we
   write them."**
4. **Indexical provenance**: are all facts timestamped / documented in a
   richer way? operatingProfile is great but must track when the claim
   was made and in what information context — e.g. currently just two
   years of AIS, "there are almost 20 to add."
5. **Dwells at scale**: dwells need a pile of attributes (first thing
   people will put on a map) — but "we'll be making a lot, surely it
   should be a data frame" (parquet), raising the RDF-vs-dataframe
   boundary question.
6. **Draft-change interpretation needs track context**: moving at speed
   + draft change → ballast change or crew reset (or long tail); at
   berth → different; at anchor → different. Suggests trying a few SQL
   views that make track analysis fast, possibly storing the DuckDB SQL
   in the capsule.
7. **Voyage**: subtle; he has no version that works for all vessels in
   his head right now.
8. **How much data in the RDF map**: structured draft values, place
   contents, etc. — "we need to work out how much actual data we should
   store in the rdf map." On places specifically he is torn between an
   application built on the capsule that generates/exposes s3 parquet
   frames vs graph contents; suspects purism ("significant data should
   not be in the map") would be massively counterproductive since some
   data hugely helps agents; wants a rule of thumb.
9. **Tow/escort as event**: will become obviously useful once
   fine-grained track analysis starts.

## Addendum (2026-07-08): Transmitter existence — state vs ephemera

Quick follow-up from James on AisIdentity/Emitter: two sensible but
different framings. In his previous work, Transmitters (physical
vessels) were usually **pre-minted from external reference data** (flag
state records, port records, commercial datasets — large systemically
important vessels like reefers were generally known there; dodgy
fishing-fleet vessels often not), and the task was matching messages TO
them — simple via MMSI, harder via MMSI sharing. When no reference
record exists and Transmitters must be inferred from AIS alone, the
predicted Transmitter set is **ephemera**: a dynamic artifact of an
analysis run that changes both as data grows AND as the automated
pipeline improves and makes different judgements. His read of our
design: a more "static" approach, pinning identities down as state and
improving the stored set over time; his: predicted-Transmitter
existence as regenerable run output, not stored state.

## Addendum 2 (2026-07-08): identity-declaration threshold + gear beacons

James confirms the three-population synthesis and restates the design:
AisIdentity is the basic unit/product of an analysis process determining
that a pattern really looks like a single Transmitter — facts hang off
it — but "this definitely is hull (Transmitter) h" is only declared
against a **solid non-AIS record** for h. (Implication for v2 naming:
an AIS-only-inferred emitter must not read as a declared hull identity;
hull declaration requires an external anchor.)

And a field reality: people use AIS transmitters to **tag fishing
gear**, released from the boat. The gear units all broadcast under the
SAME MMSI as each other (fleet-style), and put their **battery level in
the COG field**. Not made up. Implications: a benign, systematic
multi-emitter class (M2 will light up on gear fleets — distinct from
identity fraud); COG cannot be trusted as kinematics without a
plausibility screen (affects co-movement velocity alignment, track
classifiers); a genuine new object class for the menagerie.

## Addendum 3 (2026-07-08): discovery method, river shuttles, the vision

- **How the gear tags were actually found**: the beacons broadcast
  battery only in multiples of 10 (100, 90, 80 …) and discrete values
  stand out in the set — possibly first seen as peaks on a fine-grained
  regional COG histogram, then followed. The generalizable tradecraft:
  histogram a field at fine grain, hunt discrete/anomalous spikes,
  follow the thread until it becomes world knowledge. (Correction to
  the US-feed probe prior: this was likely weird Chinese kit, observed
  years ago; US-waters presence unknown, may be more common now.)
- **River shuttles as economic sensors**: some ships run between two
  (presumably) warehouses on a river, just that, year after year.
  Survey them all, find what industries the warehouses serve, and the
  fleet's activity becomes a real-time indicator: when the boats stop
  running, is that evidence of a downturn in that industry, in real
  time?
- **The vision, verbatim-ish**: "if we set up exactly the right
  conditions with this project we can throw agents at the data set and
  they'll just start learning all sorts of new things about the world."

## Addendum 4 (2026-07-08): histogram practice, SOG bimodality, Foursquare

- Histogram-shape study generalizes and should be suggested to agents
  as standing practice: he always made fine-grained histograms; the
  data volume supports very small buckets ("beautiful curves"), and the
  SHAPE of any fine-grained histogram is worth studying in itself.
- Concrete example: **SOG is two superimposed curves** — one for
  "steaming" and one for "moving at low speeds" — two different things
  captains do, visible directly in the data. (Implication: kinematic
  state thresholds can be data-derived from the valley between modes
  rather than chosen arbitrarily; refines M7.)
- **Foursquare open places** is his candidate reference dataset for
  endpoint industry identification (the shuttle-survey follow-on); he
  can load it into S3 for a study. Not settled yet.
- Session 8 is a study he has "wanted to run for many years." Boy scout
  rule endorsed for the scaling vision.

## Round 3 (2026-07-09): research question — anchor vs berth

A genuine external research question via James: **distinguish stopping
at anchor from stopping at a berth (or similar land-adjacent stop)**.
His suggested angles: (a) residual movement while "basically stopped" —
anchored vessels still move (swing), though wind-dependent; (b) pulling
OpenStreetMap data for shoreline position; "many approaches possible."
Context: M7's current berthed/anchored split leans on self-reported
status codes among non-underway days — the physical discriminator would
also grade how often NavStatus lies.
