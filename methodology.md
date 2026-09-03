# Methodology — frozen classification rules

**Frozen: 2026-09-03.**

This freeze happens before the Verus/formal-verification arm of the
experiment begins. The rules below are written down and locked now,
specifically so they cannot be tuned after either arm's results are known.
They apply symmetrically to both arms — Tiny Tapeout (this repo) and Verus.

Any change to this file after the Verus arm begins is an amendment, not a
freeze, and should be recorded as a dated addendum below the original rules,
never as a silent edit.

---

## Rule 1 — Raw hours vs. evidentiary weight

Raw friction hours are observation and **never change**.

Evidentiary weight toward the "unowned seam" thesis **may be revised
retroactively** when prior art is discovered.

Applies symmetrically to both arms.

---

## Rule 2 — Durable vs. self-closing

Any friction surviving the prior-art check (Rule 3) gets a second tag:

- **self-closing**: maintainers would plausibly fix it themselves within a
  year if someone opened an issue (missing docs, rough install, poor error
  messages). Retains observational weight, near-zero seam weight.
- **durable**: persists after onboarding matures because it is structural.

**Rationale**, recorded explicitly: absence of prior art is strong evidence
in a mature ecosystem (cocotb: a decade of docs, a populated issue tracker)
and weak evidence in a young one (Verus: a few hundred users). Without this
axis, Rule 1 strips weight from the control and preserves it on the favored
candidate for reasons that are purely about ecosystem age, not about
whether the friction is actually structural.

---

## Rule 3 — Pre-registered prior-art search protocol

Before any entry enters the "real problem" column, run and log:

- sources searched (upstream docs, issue tracker, forum/Zulip/Discord archive)
- search terms used
- time spent
- timestamp
- outcome: prior art found / not found

An unlogged search does not count. "I looked and found nothing" is
unfalsifiable after the fact.

---

## Application note

A retroactive reclassification applying these rules to friction recorded in
`friction-log.md` *before* this file existed is appended there under
"Retroactive reclassification." That section does not edit or delete any
existing friction-log entry — the raw hours already recorded stay exactly as
recorded, per Rule 1. It only adds evidentiary weight, durable/self-closing
tags, and the Rule 3 search logs that were not captured with this level of
formality at the time the original entries were written.
