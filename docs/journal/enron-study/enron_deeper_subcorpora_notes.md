# Deeper Subcorpora Notes

This pass looked below corpus-level schema and quality facts. It searched the
message-like EML population for coherent workstreams using aggregate subject,
body-surface, topic, custodian, month, and attachment-hash signals.

## Best Next Avenue: Western Power Policy

The strongest next analysis avenue is a Western power / California regulatory
subcorpus. A broad keyword view covering California, FERC, price caps, Western
market/power language, PG&E/PGE, and Calpine finds 98,087 message-like rows
across 150 custodians, 12,968 normalized subjects, and 32,486 rows with
attachments.

The time profile is coherent rather than flat:

- 2001-04: 14,487 rows, 78 custodians, 1,566 subjects
- 2001-03: 8,079 rows, 63 custodians, 1,216 subjects
- 2001-05: 7,506 rows, 93 custodians, 1,042 subjects
- 2000-11: 6,834 rows, 49 custodians, 796 subjects
- 2000-12: 5,789 rows, 73 custodians, 737 subjects

The custodian profile is also interpretable. The largest slices are
`dasovich-j` with 26,601 rows and 4,337 subjects, and `kean-s` with 20,187 rows
and 1,159 subjects. Other strong slices include `guzman-m`, `linder-e`,
`shapiro-r`, `scott-s`, `farmer-d`, and `merris-s`.

This avenue is attractive because it joins several useful evidence surfaces:
message text, subject clusters, policy/regulatory bursts, repeated body
broadcasts, and duplicate attachment hashes. It is less fragile than a pure
communication-network study because it does not depend entirely on successful
address extraction.

Examples of high-signal attachment diffusion inside this avenue include:

- `pg&e bankruptcy case-- important`: two `.doc` native-hash clusters, 94
  messages each, 44 custodians, June 2001.
- `enron's ferc filing opposing icap`: two `.doc` native-hash clusters, 24
  messages each, 19 custodians, October 2001.
- `briefing paper- ferc's june 19 west-wide price mitigation order`: 26
  messages, 10 custodians, June 2001.
- `ferc staff investigations on midwest and southeast bulk power systems`: 211
  attachment rows, 7 custodians, November-December 2000.

## Second Avenue: Collapse And Transition

A collapse/transition keyword view covering Dynegy, bankruptcy, Andersen,
Fastow, LJM, Chewco, Skilling, Ken/Kenneth Lay, credit watch, and UBS finds
49,883 message-like rows across 150 custodians, 6,258 subjects, and 13,021 rows
with attachments.

The strongest months are not only late 2001:

- 2001-05: 3,980 rows
- 2001-04: 3,951 rows
- 2001-03: 3,498 rows
- 2002-01: 3,435 rows
- 2001-11: 2,818 rows across 122 custodians

This view should be narrowed by time window before substantive interpretation,
because some terms appear before the public collapse period. It is still rich:
the repeated-body and attachment signals identify credit-watch lists, UBS
orientation documents, succession-plan broadcasts, and executive/public
communications.

High-signal repeated artifacts include:

- `credit watch list--week of 10/22/01`, `10/29/01`, and `11/19/01` with
  repeated body hashes and `.xls` attachment hashes across dozens of custodians.
- `urgent - requires immediate action - ubs orientation tomorrow @the
  houstonian`, with repeated `.pdf` attachment hashes across 24 custodians.
- `ken lay and jeff skilling on cnnfn`, 131 repeated body rows across 36
  custodians on December 13, 2000.
- `succession plan`, 129 repeated body rows across 34 custodians on December
  13, 2000.

## Third Avenue: Operational Market Plumbing

An operational-market-plumbing view covering schedule crawler, hourahead,
day-ahead, gas nomination, NWS forecast, Earthsat, and position-saving language
finds 17,640 message-like rows across 95 custodians and 1,504 subjects.

This is a compact but very structured slice. It is dominated by April 2001
with 9,005 rows, 18 custodians, and 4,499 rows with attachments. Top subjects
include `schedule crawler: hourahead failure <codesite>` and `calpine daily gas
nomination`. This is a good avenue for studying operational systems and
automated process email, but it is narrower than the Western power policy
subcorpus.

## Deeper Structural Lessons

- Topic signals are often workstreams, not just keywords. Month, custodian,
  subject, and attachment-hash structure must be used together.
- Repeated body hashes and XML `native_hash` values expose broadcast/document
  diffusion networks that are invisible in ordinary row counts.
- Some high-volume subjects are operational or calendar-like artifacts even
  after excluding obvious calendar folders.
- The best starting unit for deeper analysis is a named subcorpus with a
  documented regex/filter, not the full corpus.
- For event studies, the Western power policy track is cleaner than the
  collapse-transition track because its burst, custodian, and attachment
  signals line up more coherently.
