# What a Year of Council Spending Data Actually Looks Like

*Public-money study, article 1. Learnings from the scaffold phase:
twelve months of one English district council's published
expenditure (~950 suppliers, ~£35M), the national procurement feeds,
and the Companies House bulk register. Methodology only; the working
sessions live privately.*

The premise of transparency data is that publication equals
usability. The first thing the scaffold phase taught us is how far
apart those two things are — and that the distance is made of small,
undocumented conventions rather than anything exotic.

**The files drift.** Across twelve monthly CSVs from one body, the
header row's position varied between rows one and four; one month
replaced the blank spacer row with an FOIA notice. No two-file
sample would have revealed this — every file had to be landed before
the pattern was visible, and the loader had to become a small
detective. Lesson: for published-CSV feeds, schema discovery is a
per-file act, and every normalization must be recorded as a
transformation, because silent fixing destroys the audit trail a
tool for journalists would need most.

**Redaction has dialects.** Personal payees appear as more than one
literal form ("REDACTED Personal Expense" and a second form our
initial sample never showed). A matcher that knows one dialect
silently treats the other as a real supplier name. Lesson: redaction
literals are a vocabulary to be discovered and maintained, not a
constant.

**Negative amounts are structure, not noise.** Credits appeared in
every single month. A pipeline that filters "invalid" negative rows
quietly overstates spending; the credits are refunds, corrections,
and offsets — part of the ledger's grammar.

**Identity is the hard problem, and it comes in tiers.** Matching
supplier names to the corporate register produced a shape we now
treat as doctrine: roughly half of suppliers (and spend) resolve at
an exact tier; a quarter of spend is public-body-to-public-body
payments that should never enter company matching; a further tranche
matches only at a token-similarity tier — and the score distribution
shows a genuine empty band between the tiers, so the boundary is
empirical, not aesthetic. The discipline that follows: a token-tier
match is a *candidate carrying its features*, never a resolved
identity. Any tool that renders it as settled fact is lying with
extra steps.

**Former names carry live weight.** Dozens of exact matches exist
only through a company's previous name — including full rebrands
where nothing but the registration number connects the entities. An
entity-resolution approach without the previous-names table doesn't
just miss matches; it invents disappearances.

**Some identifiers are traps.** The body's own supplier-ID column
contained a placeholder value shared by eleven unrelated suppliers —
a key that isn't a key. And whole classes of payee (bare "Council"
names, central-government departments) have no register entry to
match against at all: the absence is structural, and a correct
system must say "not matchable in this register" rather than
degrade to fuzzy guessing.

**Verify the transfer, not the report.** The sharpest operational
lesson came from infrastructure: a standard mirroring tool uploaded
a truncated copy of a half-gigabyte file *while reporting success*,
because the source was still being written. It was caught only
because our verification streams the stored object back and
re-hashes it against a manifest, trusting neither the tool's exit
code nor the store's own checksums. For evidence-bearing data, the
manifest-and-rehash loop is not paranoia; it is the floor.

None of this is a complaint about the publishing bodies — the data
exists, which is the hard part, and its quirks are ordinary
consequences of humans exporting spreadsheets on deadline. The point
is architectural: a tool for journalists has to treat every one of
these quirks as a first-class, recorded fact with evidence attached,
because the journalist's question is never just "who was paid" but
"how sure are we, and how would we defend it." That is precisely the
discipline DoxaBase exists to mechanize, and the next phase — the
capsule field study — tests whether it transfers to this domain as
cleanly as it did to the last one.
