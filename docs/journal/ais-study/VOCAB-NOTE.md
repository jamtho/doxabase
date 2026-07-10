# VOCAB-NOTE — The aisv: Vessel-Doings Vocabulary (Session 5)

Namespace: `https://ais.study/ns#` (prefix `aisv:`). 25 terms (7 classes,
18 properties), distilled from the 20 vessel stories, 6 methods, 24 caveats
and 4 expert observations already in the capsule. Ontology-graph staged
revision `1cb51827` (applied `63a8dbb1`); proof-of-vocabulary map revision
`cca8ed52` (applied `82dcb85b`; replaces validation-failed `82e62837`,
closed superseded). Every term's `rdfs:comment` in the capsule carries the
same justifications with `rdfs:seeAlso` links.

## Vocabulary table

Story citations use the MMSI shorthand; `gen/` = the two generated-IRI
stories (0773b4ed = 367615990 JACOB BRENT/PERCIVAL, 125c7bac = 338617000
PENNSYLVANIA).

### Classes

| Term | Meaning | Justified by |
|---|---|---|
| aisv:AisIdentity | The identity keyed by one MMSI — self-reported, year-frozen, possibly describing 0..n physical objects | all 20 stories target vessel/mmsi-N; the slot-vs-hull split forced by 360000000, 999999999, 367369920 |
| aisv:Emitter | One physical AIS-transmitting object separated out of an MMSI's broadcasts | 367373000, 360000000, 999999999, 367369920, 368574000 |
| aisv:IdentityChange | The broadcast identity carried by an MMSI changes, whatever the mechanism | 311050400, 367677560, gen/0773b4ed, 366991421, 368574000, 360000000, 367369920, M1 |
| aisv:DwellPeriod | A bounded stay at one place (port call / lay-up / refit / worksite / berth) | gen/125c7bac, 311050400, 316001262, 366971370, 369305000, 338024391, 366991421 |
| aisv:SilencePeriod | A bounded period of not being received; reading is separate (silence ≠ dark) | 366971370, 538002783, 366991421, 941217116, gen/0773b4ed, M3 |
| aisv:CargoOperation | A load/discharge event inferred from a draft change at a stationary endpoint | 303520000, 538002783, 367677560, gen/125c7bac, M4, expert 6b13e8f8 |
| aisv:OperationalTie | A persistent working relationship shown by mobile co-location (M5 signature) | 369305000, 338024391, M5 |

### Properties

| Term | Meaning | Justified by |
|---|---|---|
| aisv:ofIdentity | Event/state/tie → the identity(ies) it concerns | all stories anchor to vessel/mmsi-N; multi-member by 369305000, 338024391 |
| aisv:usesMmsi | Emitter → the identity it transmits under | the five shared-MMSI stories |
| aisv:emitterKind | What the object is: vessel / fixed_installation / gear_beacon / aircraft | 368166560+367373000 (platforms), 941217116+999999999/M2 (beacons), 111227501 (aircraft — value only, single story) |
| aisv:emitterMultiplicity | How many emitters behind an identity: single / position_jitter / multi_emitter / placeholder_shared / unresolved | M2; positives 367373000/360000000/999999999/367369920; resolutions gen/0773b4ed, gen/125c7bac |
| aisv:operatingProfile | One-line behavioural characterization (metronome ferry, hub-and-spokes tanker, …) | every story's KIND line (20/20); contrastive pairs 316001262 vs 366971370, 538002783 vs 303520000 |
| aisv:startDate / aisv:endDate | Bounds of an event/period (feed UTC day granularity); for windowed changes, the real-window bounds | all dwell/silence/cargo bounds; windows 311050400, 366991421 |
| aisv:apparentDate | The date the feed displays — kept apart because annual canonicalization displaces real dates to Jan 1 | every identity story; caveat/identity-year-constant |
| aisv:datingQuality | dated / windowed / year_only_undatable | 311050400 + 366991421 (windowed), 368574000 (dated), gen/0773b4ed + 367677560 (undatable) |
| aisv:place | Where it happened: coordinates + human label, always position-inferred, never verified geocode | gen/125c7bac, 338024391, 366971370, 538002783; M4/M6 convention |
| aisv:fromIdentity / aisv:toIdentity | Broadcast identity before/after a change (name/callsign/IMO literal) | every identity story; M1's name24/name25 |
| aisv:changeMechanism | rename_same_hull / spelling_variant / mmsi_reassignment / statics_correction / slot_handover_shared_mmsi / collision_relabel / unresolved | the M1 failure-mode triptych 368574000, 360000000, 367369920 + renames + 366991421 |
| aisv:hullContinuityBasis | Evidence basis for same-hull: imo_callsign_persist / dims_and_operating_continuity / draft_continuity / position_stream_continuity / none_multi_emitter | 367677560, gen/0773b4ed, 366991421, 368574000, 367369920 (forged corroborator) |
| aisv:dwellKind | port_call / lay_up / refit / worksite_deployment / berth_stay / anchorage_wait | ≥2 stories per value; see class row |
| aisv:silenceReading | in_place_power_down / coverage_exit_voyage / gear_recovered / unexplained / implausible_jump | M3 + 366971370, 538002783, 941217116, 366991421 |
| aisv:cargoDirection | loading / discharge / ambiguous_ballast — the third value is mandatory (ballast trap) | 303520000, 538002783, 367677560, gen/125c7bac, expert 6b13e8f8 |
| aisv:tieKind | project_fleet_sisters / towed_work_spread / company_tug_pair | 369305000 vs 338024391 (explicit contrast), M5 |

## The couldn't-say list

Needs that surfaced in the harvest or the re-expression proof and were
deliberately not given terms (each is a candidate for a future revision if
≥2 more stories demand it):

1. **Observed voyages/excursions/repositionings** (367615990's two coastal
   excursions, 311050400's 1,848 km repositioning, TERESA's positioning
   voyages, GOLDEN BEAR's paired trans-Pacific legs). The closest cut: a
   `Voyage` class with from/to/distance was drafted and dropped —
   SilencePeriod covers only *unobserved* legs.
2. **Recurring event clusters / trade lanes.** Stories speak in aggregates
   ("224 events", "16+ loadings, zero discharges at the hub", "~26 cycles
   per direction"). The two NOR'EASTER CargoOperation resources had to
   stand for clusters and say so in prose. A `RecurrentPattern`/lane term
   is the single biggest gap the proof exposed.
3. **datingQuality for non-events.** The 367369920 slot handover has no
   real-world event to date; no honest value exists, the property was
   omitted. A value like `not_a_real_world_event` may be warranted.
4. **Operating-tempo metrics** (km/month, active days, duty ratio, message
   counts) — the numbers behind "metronome" and "seasonal". Candidate
   reuse: rc:ObservedProfileMetric rather than new aisv: terms.
5. **Data-quality artifacts as events** (the Wyoming fix, 303520000's
   GPS-degradation year, sub-sentinel SOG spikes, inflated mileage) — left
   to rc:Observation/rc:KnownCaveat; a per-identity quality annotation
   would still help mileage consumers.
6. **Structured draft values** (draftFrom/draftTo or bands) — dropped
   under the in-doubt-leave-it-out rule; draft bands live in prose.
7. **Place as a resource** — terminals/berths/worksites recur across
   stories (Tampa Bay appears in three), but minting a Place class means
   minting a gazetteer; kept as position-inferred literals per the M4/M6
   convention.
8. **Emitter home base** — aisv:place is event-scoped; the two clone tugs'
   bases went into prose.
9. **Tow/escort as an event** (STASINOS BOYS alongside on passage legs):
   OperationalTie carries the relationship but not individual tow legs.

Unexercised by the three-story proof (justified by harvest, not yet used
in anger): aisv:OperationalTie, aisv:tieKind, dwellKind values
worksite_deployment/anchorage_wait, silenceReading values gear_recovered/
in_place_power_down, cargoDirection value ambiguous_ballast, and
emitterKind values fixed_installation/gear_beacon/aircraft.

## Reflection (empirical distillation vs a priori design)

An a priori AIS ontology would have started with Vessel, Voyage, Port and
PortCall — and three of those four are exactly what this corpus refused to
support: "vessel" had to split into identity-slot vs physical emitter,
Voyage fell to the ≥2-story bar in observed form (most long legs here are
*silences*), and Port stayed a position-inferred literal because no story
ever verified a geocode. What the stories actually demanded — apparentDate
vs real window, hullContinuityBasis, ambiguous_ballast, silence-as-
evidence-state — are assessment terms an armchair designer would almost
certainly have omitted, and they encode this feed's hardest-won caveats.
The cost of empiricism is visible too: the vocabulary is feed-shaped (day
granularity, year-frozen identity baked into term semantics) and the
aggregate/lane gap only surfaced when re-expression was attempted. On this
corpus, distillation produced a smaller, stranger, and more honest
vocabulary than design-first would have; the couldn't-say list is the
design-first backlog, now with evidence attached.
