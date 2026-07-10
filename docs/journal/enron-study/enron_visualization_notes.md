# Enron Visualization Readout

The visual packet in `visuals/` was generated from aggregate JSON outputs, not
from raw message inspection. It is meant to test whether the deeper subcorpus
recommendation is visually supported.

## Files

- `01_candidate_subcorpora_comparison.png` compares the three candidate
  subcorpora by row count, attachment-bearing rows, custodians, and normalized
  subjects.
- `02_candidate_subcorpora_monthly_bursts.png` shows top monthly bursts for the
  three candidate subcorpora.
- `03_topic_burst_heatmap.png` shows full monthly topic counts from 2000-01
  through 2002-03 for message-like rows.
- `04_custodian_topic_matrix.png` shows log-scaled topic concentration for the
  top topic-rich custodians.
- `05_document_diffusion_hash_clusters.png` plots XML attachment `native_hash`
  diffusion by distinct custodians and attachment-row count.
- `western_power_policy/` contains the first Western power policy deep-dive
  charts.
- `western_power_policy_lanes/` contains the four-lane Western follow-up:
  lane summary, phase chart, overlap heatmap, custodian matrix, weekly peaks,
  and document-event scatter.

## What The Visuals Changed

The visuals strengthen the recommendation to start with the Western power /
California regulatory policy avenue.

The candidate comparison shows Western power policy as the broadest and richest
subcorpus: 98,087 message-like rows, 150 custodians, 12,968 normalized subjects,
and 32,486 rows with attachments. Collapse/transition is also broad but about
half the size by rows and subjects. Operational market plumbing is highly
structured but much narrower.

The monthly burst chart separates the candidates cleanly:

- Western power policy has a sustained ramp from 2000-08 through 2001-05 and a
  strong April 2001 peak.
- Collapse/transition is more diffuse, with pre-collapse signal in early 2001
  and later spikes in 2001-11 and 2002-01.
- Operational market plumbing is dominated by a sharp April 2001 spike, which
  makes it attractive for a focused operational-systems study but less suitable
  as the first broad case study.

The corrected topic heatmap shows California and FERC as sustained tracks, not
single-month anomalies. It also shows LJM/Fastow as much more event-like, with
the strongest concentration in October 2001. That suggests the collapse track
should be analyzed as a narrower event window, while Western power policy can
support a longer process/history analysis.

The custodian-topic matrix makes the main roles more legible:

- `dasovich-j` and `kean-s` dominate the California/FERC policy area.
- `guzman-m`, `linder-e`, and `merris-s` are much more California-specific.
- `lay-k` is unusually bankruptcy-heavy relative to many other topics.
- `kitchen-l` is comparatively stronger on Fastow/LJM than on California/FERC.

The attachment-hash diffusion plot confirms that document diffusion is a
separate evidence layer. The Western policy track has identifiable clusters
such as FERC investigations and PG&E bankruptcy documents, while the
collapse/transition track has credit-watch and UBS orientation artifacts. These
are better modeled as document-spread events than as ordinary email threads.

The Western lane visualizations sharpen that recommendation. April 2001 is
operationally different from the late-2000 regulatory ramp: ISO / market
plumbing dominates the April spike, while FERC/regulatory and document/news
lanes dominate the preceding ramp and later aftermath. The overlap heatmap also
shows that FERC and document/news are heavily intertwined, so document diffusion
should be modeled explicitly rather than treated as background noise.

## Recommended Follow-Up

Build a named Western power policy subcorpus and analyze it as a diffusion
study:

1. Define the filter using California/FERC/price-cap/Western power/PG&E/Calpine
   terms.
2. Deduplicate with `doc_id`, `body_top` hash, and XML attachment `native_hash`.
3. Track month, custodian, normalized subject, and attachment hash.
4. Separate recurring operational artifacts from policy/regulatory documents.
5. Compare custodian roles, especially `dasovich-j`, `kean-s`, `guzman-m`,
   `linder-e`, `merris-s`, `shapiro-r`, and `scott-s`.

The collapse/transition track remains a strong second study, but it should be
time-windowed around October 2001 through February 2002 and split into
credit-watch, UBS transition, Fastow/LJM, and bankruptcy subthreads.
