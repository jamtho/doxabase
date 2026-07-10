# Western Power Policy Lane Analysis

This note summarizes a second pass over the Western power / California policy
subcorpus. The supporting aggregate data is in
`western_power_policy_lanes.json`; charts are in
`visuals/western_power_policy_lanes/`.

The four lanes are multi-label working cuts, not mutually exclusive classes:

- Operational ISO / market plumbing: ISO, CAISO, schedules, hour-ahead,
  day-ahead, congestion, bids, imbalance, market operations, and Calpine/gas
  nomination language.
- FERC / regulatory policy: FERC, refunds, price caps, mitigation, orders,
  comments, investigations, tariffs, proxy prices, and related regulatory
  language.
- PG&E / credit / bankruptcy: PG&E/PGE, bankruptcy, credit, liquidity, exposure,
  default, utilities, DWR, San Diego, Edison, and related counterparty-risk
  language.
- Document / news diffusion: newsletters, reports, filings, memos, articles,
  presentations, repeated body hashes, and repeated XML attachment hashes.

Because the same email can carry an operational fact, a regulatory issue, and a
forwarded document, overlap is part of the evidence rather than an error.

## Lane Sizes

The parent Western slice contains 107,510 message-like rows across 149
custodians and 14,340 normalized subjects.

- Operational ISO / market plumbing: 37,017 rows, 69 custodians, 12,063 rows
  with attachments, 2,196 repeated-body rows, 1,521 repeated-attachment rows.
- FERC / regulatory policy: 50,921 rows, 113 custodians, 15,357 rows with
  attachments, 2,921 repeated-body rows, 4,256 repeated-attachment rows.
- PG&E / credit / bankruptcy: 35,367 rows, 117 custodians, 8,674 rows with
  attachments, 1,402 repeated-body rows, 1,877 repeated-attachment rows.
- Document / news diffusion: 47,658 rows, 141 custodians, 17,967 rows with
  attachments, 5,281 repeated-body rows, 7,592 repeated-attachment rows.

The document/news lane has fewer total rows than FERC but the strongest
repeated-text and repeated-attachment surface. It is best treated as a carrier
layer that crosses the other lanes.

## Time Structure

The phase chart makes the Western story less monolithic:

- Pre-ramp through late 2000 is regulatory/document-heavy. In the late-2000
  ramp, FERC has 17,302 rows and document/news has 16,218 rows.
- April 2001 is operationally distinct. Operational ISO / market plumbing jumps
  to 9,826 rows, far above FERC at 3,885 and PG&E/credit at 3,213.
- Mid-2001 aftermath shifts back toward regulatory and document circulation:
  document/news has 8,331 rows and FERC has 7,281 rows.
- Q1 2002 is a smaller tail, with operational and PG&E/credit signal still
  present but much lower than the 2000-2001 crisis period.

The top weekly peaks reinforce that split:

- Operational ISO / market plumbing peaks in April 2001, especially weeks of
  2001-04-16 and 2001-04-23.
- FERC / regulatory policy peaks around 2000-12-11 and 2000-11-06, then recurs
  during March-April 2001.
- PG&E / credit / bankruptcy has a later 2002-01-28 peak as well as March-May
  2001 activity.
- Document/news diffusion peaks around 2000-12-11 and stays strong across
  March-May 2001.

## Overlap

The largest lane overlaps are informative:

- FERC + document/news: 31,436 rows.
- FERC + PG&E/credit: 19,477 rows.
- PG&E/credit + document/news: 18,686 rows.
- Operational + FERC: 16,413 rows.
- Operational + document/news: 15,565 rows.
- Operational + PG&E/credit: 10,110 rows.
- Operational + FERC + PG&E/credit: 8,038 rows.

This suggests that FERC/regulatory policy is often carried by circulated
documents and news, while operational ISO activity becomes central during the
April 2001 peak. PG&E/credit is not a separate isolated thread; it is tied into
both regulatory and document-diffusion channels.

## Custodian Roles

The custodian-lane matrix separates roles more clearly than the original
subtopic counts:

- `dasovich-j` and `kean-s` are broad policy/document hubs, especially strong
  in FERC/regulatory and document/news diffusion.
- `guzman-m`, `linder-e`, `merris-s`, `williams-b`, `meyers-a`, and
  `solberg-g` are much more operational-ISO oriented.
- `farmer-d` is operational and document-heavy, consistent with the Calpine and
  counterparty-operation surface.
- `lay-k` is relatively stronger in PG&E/credit than many other custodians.
- `shapiro-r`, `scott-s`, `hain-m`, `kaminski-v`, and `symes-k` are mixed
  regulatory/policy profiles worth using as bridge custodians.

Sender-domain coverage remains too sparse for the primary analysis. Coverage is
15,356 of 37,017 operational rows, 7,404 of 50,921 FERC rows, 5,166 of 35,367
PG&E/credit rows, and 8,063 of 47,658 document/news rows.

## Subject And Document Events

Top subjects make the lane semantics concrete:

- Operational: `calpine daily gas nomination`, `schedule crawler: hourahead
  failure <codesite>`, `calpine daily gas nomination (weekend)`, plus
  operationally adjacent FERC/California threads.
- FERC: `enron mentions`, `energy issues`, `weekly ferc electric report`, San
  Diego gas price cap comments, comments on FERC orders, and Western wholesale
  activity reviews.
- PG&E/credit: Kaufman weekly calls about sale of PGE, `pg&e`, financial
  analysis of PG&E, and related credit/bankruptcy subjects.
- Document/news: `enron mentions`, `energy issues`, `california power issue`,
  `entouch newsletter`, `weekly ferc electric report`, and repeated attachment
  events.

The strongest document events should become named case studies:

- PG&E bankruptcy documents: two `.doc` attachment hashes on `pg&e bankruptcy
  case-- important`, around 90 rows each across 44 custodians in the lane pass.
- FERC staff investigations on Midwest and Southeast bulk power systems: large
  repeated attachment hashes in the regulatory/document layer.
- Enron's FERC filing opposing ICAP: 24 rows across 19 custodians.
- California energy crisis: repeated body hash with 51 rows across 17
  custodians.
- Briefing paper on FERC's June 19 West-wide price mitigation order: repeated
  attachment event in the regulatory lane.

## Recommended Next Case Studies

1. April 2001 operational ISO / market spike. Start with weeks of 2001-04-16
   and 2001-04-23, then trace `schedule crawler`, hour-ahead/day-ahead, ISO,
   bids, Calpine, and gas-nomination subjects across `guzman-m`, `linder-e`,
   `merris-s`, `williams-b`, `meyers-a`, and `solberg-g`.
2. Late-2000 FERC regulatory ramp. Start with weeks of 2000-12-11 and
   2000-11-06, then inspect FERC orders, price caps, San Diego gas price caps,
   mitigation, refunds, and staff investigation documents.
3. PG&E bankruptcy and credit diffusion. Start from the repeated PG&E
   bankruptcy attachment hashes and trace which custodians received, forwarded,
   or discussed those documents.
4. Document/news carrier layer. Treat repeated `body_top` hashes and XML
   `native_hash` values as first-class events, then connect those events back
   to the operational, FERC, and PG&E lanes.

## Caveats

These lanes are keyword-built and intentionally broad. A qualitative pass should
inspect sampled messages before asserting intent or policy position. Repeated
body hashes can represent forwarded articles, newsletters, or parser artifacts,
so blank-subject or unusually long repeated-body clusters need direct review.
Network claims should wait for better sender/recipient extraction coverage.
