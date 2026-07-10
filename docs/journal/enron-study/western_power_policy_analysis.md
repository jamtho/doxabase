# Western Power Policy Deep Dive

This note summarizes a deeper aggregate analysis of a Western power /
California regulatory policy subcorpus in the Enron email data. The supporting
tables are in `western_power_policy_deep_dive.json`; the charts are in
`visuals/western_power_policy/`.

## Definition

The slice starts from EML message-like rows dated from 1999-01 through 2002-03,
excluding calendar, contacts, and meetings folder families. It then matches
Western power policy terms such as California, FERC, price caps, mitigation,
refunds, proxy prices, PG&E/PGE, Calpine, DWR, CAISO/Cal-ISO, Western crisis,
and West-wide power-market language.

This is a keyword-defined working subcorpus, not a final labeled dataset. The
terms intentionally over-capture adjacent operational and counterparty threads
so that the first pass can expose structure.

## Headline Shape

- 107,510 message-like rows
- 149 custodians
- 14,340 normalized subjects
- 34,506 rows with attachments
- 98,830 rows with `body_top`
- 103,445 rows with `body`

Main subtopic counts overlap:

- California: 69,538 rows
- PG&E / bankruptcy: 30,026 rows
- FERC: 28,121 rows
- ISO / markets: 27,335 rows
- price caps / mitigation: 13,571 rows
- Calpine: 10,754 rows
- DWR: 5,807 rows
- Western-market phrasing: 1,836 rows

Important overlaps:

- California + ISO / markets: 23,035 rows
- California + PG&E: 15,687 rows
- California + FERC: 13,102 rows
- California + price caps: 8,614 rows
- FERC + price caps: 7,866 rows
- PG&E + FERC: 6,584 rows

## Temporal Structure

The visual timeline shows a sustained ramp from late 2000 into a sharp April
2001 peak. The peak month is 2001-04 with 15,064 distinct rows. The highest
weeks are:

- week of 2001-04-23: 4,465 rows, 60 custodians
- week of 2001-04-16: 4,035 rows, 54 custodians
- week of 2001-04-09: 3,321 rows, 50 custodians
- week of 2000-12-11: 2,759 rows, 55 custodians
- week of 2001-04-02: 2,512 rows, 46 custodians

The April 2001 peak is not only a generic "California" spike. It is heavily
loaded with ISO / market language, with PG&E, FERC, and price-cap material
distributed around the broader late-2000 through mid-2001 ramp.

## Custodian Roles

The custodian role matrix suggests several distinct roles:

- `dasovich-j`: broadest policy/regulatory slice. 28,182 rows, 4,613 subjects;
  strong across California, FERC, PG&E, price caps, DWR, Calpine, and Western
  market terms.
- `kean-s`: similarly broad, with 23,045 rows and especially strong FERC,
  price-cap, PG&E, and Western-market signal.
- `guzman-m`, `linder-e`, `merris-s`, `williams-b`: concentrated in
  California/ISO-market activity, with less FERC/PG&E breadth.
- `farmer-d`: dominated by Calpine and attachment-heavy operational/counterparty
  material.
- `scott-s`: comparatively stronger in FERC, PG&E, and Calpine than in ISO
  operations.
- `shapiro-r`, `hain-m`, `kaminski-v`, `symes-k`: mixed regulatory/policy
  profiles with useful breadth.

This is a better starting point than a sender-recipient network. Sender-domain
coverage is only 25,856 of 107,510 rows, so network analysis would be a partial
view unless address extraction is improved.

## Workstream Structure

Top subject workstreams split into several types:

- Recurring operational/counterparty artifacts: `calpine daily gas nomination`,
  `schedule crawler: hourahead failure <codesite>`.
- Policy/regulatory working calls: `fyi - p kaufman weekly call w/ regulatory
  re sale of pge...`, `fyi - weekly california conf call...`, `project
  california daily conf call`.
- News/policy-monitoring flows: `enron mentions`, `energy issues`, `entouch
  newsletter`, `weekly ferc electric report`.
- Event/documents: `pg&e`, `california power issue`, FERC order/comment threads.

This means the slice should be split again before qualitative analysis:
operational market plumbing, regulatory strategy, news monitoring, and document
diffusion are related but analytically different.

## Document Diffusion

Repeated body hashes and XML attachment `native_hash` values identify diffusion
events that row counts alone miss.

Strong document events include:

- `pg&e bankruptcy case-- important`: two `.doc` attachment hashes with 94 rows
  each across 44 custodians, June 2001.
- `enron's ferc filing opposing icap`: two `.doc` attachment hashes with 24
  rows each across 19 custodians, October 17, 2001.
- `california energy crisis`: body hash with 51 rows across 17 custodians on
  March 13, 2001.
- `california department of water resources`: body hash with 18 rows across 18
  custodians on November 19, 2001.
- `briefing paper- ferc's june 19 west-wide price mitigation order`: attachment
  hash with 26 rows across 10 custodians, June 2001.

There are also repeated body hashes with blank subjects and very long bodies.
Those should be inspected carefully before interpretation; they may represent
newsletters, pasted articles, or body-parsing artifacts.

## Best Follow-Up

The most promising next study is not a social-network graph. It is a
workstream-and-document diffusion study:

1. Build a cleaned Western policy subcorpus with explicit subtopic flags.
2. Split it into four lanes: operational ISO/market plumbing, regulatory/FERC
   policy, PG&E/credit/bankruptcy, and document/news diffusion.
3. Use `doc_id` for identity, `body_top` hash for repeated text, and XML
   attachment `native_hash` for document diffusion.
4. Use month/week and custodian role matrices as the primary spine.
5. Treat sender-domain analysis as secondary until extraction coverage improves.

The April 2001 California/ISO peak and the June 2001 PG&E bankruptcy document
diffusion are especially good first case studies because they are visible in
multiple evidence surfaces: time, custodian roles, subjects, attachments, and
repeated text.

## Follow-Up Lane Pass

The recommended split has now been run. See
`western_power_policy_lane_analysis.md`, `western_power_policy_lanes.json`, and
`visuals/western_power_policy_lanes/`. The main refinement is that April 2001
is operationally distinct, while the late-2000 ramp is more regulatory and
document/news driven.
