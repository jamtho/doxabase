# Design Doc 16: Policy as Capsule Citizen

**Date**: 2026-08-11
**Status**: FIRST ATTEMPT, explicitly subject to change as evidence
arrives — the second-person corpus, the federated experiments, and the
public observatory will each stress this design before it hardens.
Written now because the owner named the thesis and the pilot has
already produced the first three mechanical gaps that prove the need.
**The thesis (the owner's)**: "a mixture of nuanced, flexible policy
writing and nuanced, flexible provenance tracking will surely be a big
part of this product going forwards, especially if it scales up into
some sort of federated system."

---

## 1. The problem, from lived evidence

Every protection currently in force in this project is a **prose rule
in one agent's memory**: the four redaction families (no employer
concept, no family members, no private-domain nouns, no
credentials/infrastructure); person-model content only under recorded
consent with indexicality conditions; private-first routing for
owner-profile material with "any doubt defaults to doubt";
absence-by-request ("best not write it down" — honored recursively);
removals executed silently. These work — the pilot's harvests applied
them across five tranches with zero substantive leaks — but only
because a single agent is the sole write path and enforcement point.

Three mechanical gaps have already surfaced where the prose rule and
the machinery disagree:

1. `export_preflight` does not recognize person-model content as a
   category — consented-private material would ride along in an
   export if older residues were cleared (PROMOTE-1 friction §4).
2. The scanner counts history-retained matches identically to live
   ones, so a *repaired* leak looks like a present one and a gate
   cannot distinguish them (HARVEST-3 friction).
3. The observatory bundle's "local-only pending review" is a manifest
   *stamp*, not an enforcement — nothing stops a stamped bundle being
   served (observatory MVP, noted at build).

And one structural fact: the moment a second capsule, second person,
or second serving surface exists, the single-enforcement-point model
is gone. The friend corpus (arriving now) brings a second consent
regime; federation brings arbitrarily many.

## 2. The design bet

**Policies become graph citizens**: written, evidenced, revisable
statements living in the capsule they govern, subject to staged review
like any other claim, and **enforced mechanically at boundaries**
(export, serving, cross-capsule reference) by engines that read them.

The layering follows doc 12's proven pattern, because consent
semantics will not fit hard shapes alone:

- **L0 — the policy prose** (mandatory, human-audited): "material
  modelling a person's behaviour may be recorded only under that
  person's informed consent, must carry assessment windows, and may
  not leave this capsule without per-artifact approval by the
  subject." The nuance lives here; a policy whose prose disagrees
  with its structure is a bug in the policy.
- **L1 — the structured contract**: what the policy GOVERNS (content
  categories, by type/predicate/namespace patterns — e.g. "instances
  of kh:PersonModelClaim and anything reachable from khperson: via
  aboutPerson"), what it PERMITS/REQUIRES/FORBIDS per **boundary**
  (record-time, export, serve, cite-from-another-capsule), and on
  whose AUTHORITY (the consent observation's IRI — policies cite
  their consent evidence exactly as claims cite theirs).
- **L2 — parameters**: the revisable specifics (which namespaces, the
  scanner patterns, review-required flags), evidenced and dated so a
  policy's scope ages visibly.
- **L3 — enforcement realizations**: the code that enforces at each
  boundary (`export_preflight` growing into the reference policy
  engine; the workbench/observatory serving checks; a future
  federation gateway), each labelled as ONE realization of the
  policy contract — testable against it, replaceable.

Provenance is the enforcement substrate: a policy engine can only
honor "nothing derived from X leaves without review" if derivation is
tracked — which the capsule already does better than anything else in
the stack (evidence chains, derivedFromRun, fromObservation,
supersession). **Policy is the read-side consumer the provenance
machinery has been waiting for.**

## 3. What the first policies would be (distill, don't design)

Per standing law, the policy vocabulary gets distilled from the
policies actually in force, not invented. The first corpus is already
written: the four families, person-model consent, private-first
routing, absence-by-request, silent removals, the observatory's
review stamp, the AIS study's shareability flow (scanner-clean ≠
export approval — the oldest policy in the project). Eight-ish real
policies with real enforcement histories, including violations caught
(the prose-scanner false positive, the tombstone commit messages that
had to be silenced). That is enough to distill honestly.

## 4. Federation, sketched only as constraints

No federation design here — only what policy-as-citizen must make
true for it ever to work: (a) policy travels WITH data — a capsule
fragment shared across a boundary carries the governing policies and
their consent evidence, machine-readably; (b) the receiving side can
EVALUATE before accepting (do I honor per-artifact review? can I?);
(c) revocation propagates — consent withdrawal is a staged revision
whose effect crosses the same boundaries the data did; (d) audit is
symmetric — both sides can show what policy permitted any given flow.
The concurrent-capsule lanes/quarantine thinking is the intra-org
version of the same machinery.

## 5. Honest unknowns

Whether policy evaluation belongs in SHACL at all or wants its own
engine (lean: own engine, SHACL for the structural halves); how
category membership is decided for prose content (the person-model
category is easy — typed; "anything about the owner's life" is not);
policy conflicts (two policies, one artifact — precedence needs its
own semantics); the performance of reachability-based categories at
scale; and whether policy prose can be made testable the way method
contracts were (the A/B pattern — give an agent only the policy and
see if it enforces correctly — is probably the right trial design).

## 6. Immediate, cheap, already-justified steps

1. `export_preflight`: recognize typed categories (person-model
   first) and distinguish live vs history-retained matches — the two
   ledgered gaps, fixed as the first L3 realization.
2. Record the eight in-force policies as L0 prose citizens with their
   consent/authority citations — no new vocabulary yet, just the
   corpus the distiller will need.
3. When the friend corpus lands: write its consent as the first
   SECOND-REGIME policy citizen and let the two regimes coexist —
   the first real test of per-capsule policy scoping.
