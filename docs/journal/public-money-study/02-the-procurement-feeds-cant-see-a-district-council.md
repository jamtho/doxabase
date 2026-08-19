# The National Procurement Feeds Can't See a District Council

*Public-money study, article 2. Learnings from the procurement
cross-reference: twelve months of one English district council's
expenditure joined against the UK's two national procurement
platforms. Methodology only; the working sessions live privately.*

After "who was paid," the journalist's next question is "was it
procured?" — is there a published tender or award behind the
payments? The assumption embedded in that question is that
procurement records are *look-up-able*: that somewhere there is a
page per public body listing its contracts. What we found instead is
a chain of structural surprises, ending in a negative result we can
now defend properly — which is the point.

**There is no buyer filter.** Neither national platform's API can be
asked "show me this council's notices." One accepts only
limit/cursor/date-window/stage parameters; the other only
published-date windows, stages, and cursors. We confirmed this
against both live documentation pages before fetching anything,
because "the parameter I want doesn't exist" and "I didn't find the
parameter" are different claims. The only body-scoped pull is
therefore a crawl of the entire national feed, filtered client-side
— every question about one small council costs a walk through
everyone's notices.

**The cheap route is broken in a misleading way.** One platform
documents a bulk CSV harvester — one request per day of data, vastly
cheaper than paginating. Called live on four dates spanning our
window, every request returned HTTP 200 — success — with an empty
body and a content-disposition filename of `export-error.csv`. A
pipeline checking status codes would record four successful
downloads of nothing. The error channel here is a *filename*.

**The real rate limits are undocumented.** Both APIs began returning
HTTP 429 after roughly 10–17 consecutive requests, at 2-second and
4-second spacing alike — a request-count limiter, not a rate
limiter, so politeness doesn't help. Neither help page documents
this numerically; both document a different failure case we never
triggered. Escalating backoff recovers cleanly, but the practical
budget for a national crawl becomes wall-clock time, not request
count — worth knowing before promising a journalist "we'll just
pull the feed."

**Pagination has epistemics.** Both feeds return newest-first, so a
time-budgeted crawl covers the most recent months completely before
the earliest ones — partial coverage is at least *contiguous and
describable*, never a random sample. And completion has a signature:
a genuine last page arrives short (fewer releases than the page
limit) with no next-cursor. Mid-series, one platform handed us
something else: a full page — 100 releases, valid JSON — with the
pagination links object simply absent. Deterministic, reproduced
four times against the identical cursor. Treating it as "no next
page" would have silently amputated months of coverage while looking
exactly like success. The workaround: the cursor encodes the query's
own date window, so a fresh query with a narrower end-date opens a
new cursor space; we landed the continuation as its own dataset and
de-duplicated across the seam by release identifier, rather than
silently merging two crawls into one story.

**We shipped one of these bugs ourselves.** Our crawler's
documentation said "resumable, idempotent per page." It wasn't: on
re-invocation it deleted its landed pages and restarted from the
newest — which, against a newest-first feed, would have re-walked
the same pages to the same stopping point forever, extending nothing
while reporting work. The bug was findable *because the record made
a checkable claim* — the fix was verified with a 30-second live run
(nine new pages, all genuinely older than the previous stop, zero
re-fetches) before any real crawl was trusted with it. Tools that
document their own guarantees hand you the test for free.

**The finding: one notice in twelve months.** With one platform's
full year finally closed — verified by the genuine-last-page
signature *and* a scan for date gaps across all landed pages — the
council appears as a buyer in exactly **one** national notice. Of
the ~40 suppliers we had resolved to registered companies, **zero**
are corroborated by a council-buyer national notice. Of 282 rows in
the council's own published contract register, **zero**. And 228 of
282 suppliers paid at least £10k over the year — **£18.6M** of spend
— have no procurement trace by any of our three methods:
expenditure, register join, national-notice join.

The crucial move is what happened when coverage grew. These numbers
were first computed on a partial crawl; a skeptic should say "you
just haven't fetched the months where the notices are." Then the
platform's covered months doubled to the full year, the other's more
than doubled — and every number came back identical. *Unchanged
under much fuller coverage* is what converts a partial-coverage
artifact into a finding. Our views now carry both evidence bases in
their descriptions rather than overwriting the old with the new.

The finding is also not scandal — and saying so precisely is the
discipline. The platforms have publication thresholds (roughly £100k
per contract on one, £12k on the other), and a district council's
supplier base is overwhelmingly local trades and small firms below
both. The national feeds are structurally near-blind to small-body
procurement; most of that £18.6M is plausibly *below the floor*, not
hidden. So every absence claim in the capsule is worded as scoped
absence: "no record found by these methods, over this coverage, as
of this date" — never "no procurement record exists." For a
journalists' tool this is the load-bearing lesson of the whole
phase: an absence is a claim about your methods and your coverage,
and a tool that reports absences without carrying their coverage
basis is manufacturing false stories on both sides — phantom
scandals where records sit below thresholds, and false clearances
where the crawl simply stopped early.

None of this required anything exotic — just the habit of treating
the fetch layer itself as evidence: documentation checked live,
error channels discovered empirically, completion signatures
distinguished from anomalies, our own tooling's claims tested like
anyone else's. The next article will look at what happened when we
ran cold agents against the growing capsule to measure whether any
of this recorded know-how actually transfers.
