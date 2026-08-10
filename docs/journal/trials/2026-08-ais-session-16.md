# AIS Study — Session 16: M14, the Placeholder Segregator (2026-08-10)

The queued-since-July session: the expert's round-1 segregation
tradecraft (position infers identity) made mechanical against the
placeholder-MMSI population, under doc-14's candidate-emitter law.
Graph conforms, zero staged debt; journal JOURNAL-16.md; IRIs in
work/m14/recorded_iris.json.

## The census surprise

Screening the full 91,977-MMSI stops population against the recorded
MMSI-structure families found **35 placeholder MMSIs, not the 7 known**
— 18,246 stop events (2.55× the known figure). The single largest,
**444444444** (3,794 stops), was previously unknown and beats every
known placeholder. The screen, not the anecdote list, is now the
census instrument.

## Segregation and the proof case

Top-3 by volume segregated (542k messages total; deterministic,
byte-identical reruns, all four contract invariants verified exact):
444444444 → 2 tracks; 982000000 → 3; 310000000 → 27 (honestly
fragmented — the caveat records both under- and over-segmentation
directions with evidence). All three broadcast one literal identity
tuple across their whole 2-year life — hardcoded transponder-firmware
defaults, not owner data. The proof case is clean: 444444444's two
tracks share the identical "M/Y CASUAL" identity, so only kinematics
separates them — five cross-track message pairs within 600s imply
149–319 kn (impossible for one object), corroborated by a categorical
transceiver-class split. Plot: work/plots/m14_444444444_proof_case.png.

## The doc-14 law, exercised at population scale

31 candidate emitters stay in frames; exactly ONE promoted —
444444444's dominant track — as an aisv:Emitter with an anchor
descriptor. The gear-beacon check ran and returned a recorded
NEGATIVE (COG spans continuously; multiples-of-10 below chance — the
opposite of the confirmed 941217116 signature): the honest-negative
practice holding.

## Recorded

M14 pattern + doc-12 contract (reusing M12's glitch-speed parameter by
reference — third cross-contract reuse), 3 datasets/11 columns, 1 new
caveat, 4 claims, 1 profile observation. Friction: one performance
trap (row-wise DuckDB inserts; fixed vectorized), zero product bugs —
the targeted errors self-corrected the one bad call.
