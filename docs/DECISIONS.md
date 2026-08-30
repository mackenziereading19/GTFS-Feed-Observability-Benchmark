
Decision Log
D-001 — 2026-08-30 — Begin with snapshot evidence

Decision: Build a deterministic single-feed manifest before implementing
change detection.

Reason: Longitudinal conclusions are only defensible if each source
snapshot is independently reproducible.

D-002 — 2026-08-30 — Standard-library-only V0

Decision: Use only Python standard-library components for the initial
scanner.

Reason: Keeps the first feasibility layer portable, inspectable and free
from installation dependencies.

D-003 — 2026-08-30 — No health score

Decision: Do not collapse metrics into a synthetic health score.

Reason: A score would embed normative assumptions before empirical
evaluation has established which longitudinal changes are meaningful.

D-004 — 2026-08-30 — Reuse frozen Wellington feed as first fixture

Decision: Test V0 against the already-frozen Mobility Database feed
mdb-1132.

Reason: Its provenance and SHA-256 were independently established during
the GTFS next-four-weeks feasibility investigation, so it provides a useful
known input without another download.

## D-005 — 2026-08-30 — Controlled pairwise comparison before live history

**Decision:** Validate the first manifest comparator against a deterministic
derived fixture with known changes before comparing two independently
published real-world feed versions.

**Reason:** A controlled fixture provides exact expected deltas and prevents
misinterpreting comparator defects as real-world feed behaviour.

The controlled fixture changes only:

- removal of `transfers.txt`;
- addition of one unused synthetic stop;
- `feed_end_date` from `20260926` to `20261003`;
- maximum `calendar.txt` end date from `20261031` to `20261107`;
- one additional `calendar_dates.txt` row dated `20261003`.

The fixture is test infrastructure only and is not evidence about the real
Greater Wellington feed.

## D-006 — 2026-08-30 — Real longitudinal comparison establishes non-zero signal

**Decision:** Retain the Santa Monica / Big Blue Bus two-version comparison as
the first real longitudinal feasibility evidence.

**Inputs:**

- official City of Santa Monica / Big Blue Bus historical GTFS archive;
- `gtfs_20190818-20200215.zip`;
- `gtfs_20200216-20200523.zip`;
- both genuine publisher archive objects;
- older archive recovered through GitHub's media endpoint because it is stored
  through Git LFS.

**Observed transition:**

- routes: 22 -> 20;
- trips: 3,720 -> 3,563;
- service IDs used by trips: 14 -> 10;
- stops: 924 -> 923;
- stop_times rows: 130,168 -> 129,412;
- shapes rows: 20,239 -> 21,485;
- no GTFS tables added or removed;
- feed and calendar temporal bounds advanced into the new publication period.

**Interpretation:**

The deterministic comparison produces genuine longitudinal evidence on a real
publisher transition. This supports continuing feasibility work.

However, aggregate row and entity counts do not yet establish a strong
observability niche over ordinary GTFS diff tooling. The next useful gate is
identity-aware change: determine which route, stop and service IDs were added
or removed rather than merely reporting count deltas.

Do not add health scoring, anomaly thresholds or normative interpretations at
this stage.

The Santa Monica evidence represents historical publisher behaviour and must
not be interpreted as a current feed-quality assessment.

## D-007 — 2026-08-30 — Identity-aware comparison exposes hidden identifier churn

**Decision:** Retain identity-aware route, stop and service-ID comparison as a
useful longitudinal capability.

**Real-feed evidence:**

For the Santa Monica / Big Blue Bus transition from
`gtfs_20190818-20200215.zip` to `gtfs_20200216-20200523.zip`:

- route count changed only from 22 to 20, but:
  - 20 route IDs were added;
  - 22 route IDs were removed;
- stop count changed only from 924 to 923, but:
  - 8 stop IDs were added;
  - 9 stop IDs were removed;
- service IDs used by trips changed from 14 to 10:
  - 0 were added;
  - 4 were removed.

**Interpretation:**

Net entity-count deltas conceal substantial identifier churn. This supports the
value of identity-aware longitudinal evidence beyond aggregate row counts.

However, a removed GTFS identifier must not be interpreted as proof that the
underlying service, route or stop was withdrawn. GTFS identifiers are
publisher-controlled and may be regenerated between feed versions.

For routes in particular, the near-total replacement of the ID namespace means
the next useful feasibility gate is semantic continuity matching: determine
whether old and new route IDs represent the same apparent routes using stable
descriptive attributes.

Do not add fuzzy matching, health scoring, anomaly thresholds or claims of
service withdrawal until continuity behaviour has been evaluated.
