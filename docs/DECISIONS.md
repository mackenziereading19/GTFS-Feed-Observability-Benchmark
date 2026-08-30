
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

## D-008 — 2026-08-30 — Route semantic continuity resolves apparent ID churn

**Decision:** Retain conservative route semantic-continuity analysis as a
distinct longitudinal observability capability.

**Real-feed evidence:**

For the Santa Monica / Big Blue Bus historical transition:

- no route IDs persisted;
- 22 old route IDs disappeared;
- 20 new route IDs appeared;
- 20 old/new route pairs are exact matches when `route_id` is excluded from the
  complete `routes.txt` row;
- exact semantic continuity covers 20/22 old routes (90.9%);
- all 20 candidate routes have an exact semantic predecessor (100%);
- no ambiguous semantic groups occurred;
- only two baseline routes remain unmatched;
- the conservative core-field signature yields exactly the same result.

**Interpretation:**

The raw identifier transition substantially overstates underlying route
change. Twenty apparently removed routes and twenty apparently added routes
are semantically identical route definitions with regenerated identifiers.

This demonstrates why longitudinal GTFS observability should distinguish:

1. aggregate entity-count change;
2. raw identifier churn;
3. semantic continuity.

A removed `route_id` is therefore not evidence of service withdrawal.

The next gate is forensic examination of the two unmatched baseline routes.
Do not introduce fuzzy matching or infer withdrawal until those cases are
understood.

## D-009 — 2026-08-30 — Unmatched routes are bounded exception-only services

**Decision:** Retain forensic analysis of unmatched route-continuity cases and
record effective service dates rather than inferring route withdrawal from
identifier absence.

**Cases:**

### Route 20 / baseline route_id 3075

- `route_short_name`: `20`;
- `route_long_name`: `Dwtn LA Expo Shuttle`;
- 48 trips;
- sole service ID: `84310`;
- no regular weekdays are active in `calendar.txt`;
- service is supplied entirely through five `calendar_dates.txt` additions;
- effective service dates are 2019-08-19 through 2019-08-23;
- no candidate route in the succeeding feed has short name `20`;
- candidate stop-set overlap is zero for the highest-ranked alternatives.

### Route 45 / baseline route_id 3082

- `route_short_name`: `45`;
- `route_long_name`: `SM Pier Shuttle`;
- 135 trips;
- service IDs: `41401`, `41402`, `41410`;
- none has regular weekdays active in `calendar.txt`;
- service is supplied through exception additions;
- combined effective service span is 2019-08-18 through 2019-09-01;
- no candidate route in the succeeding feed has short name `45`;
- candidate stop-set overlap is negligible.

**Interpretation:**

The two routes left unmatched by semantic route continuity are temporally
bounded exception-only services. Their nominal calendar rows span the full
feed period, but their effective service exists only on a small set of added
dates.

This demonstrates another observability distinction:

1. declared calendar bounds;
2. effective service dates after exceptions;
3. semantic continuity into the succeeding feed.

The evidence supports describing these routes as bounded services absent from
the succeeding publication. It does not independently establish the policy or
operational reason for their absence and should not be labelled as service
withdrawal without external evidence.

Do not generalise candidate ranking into fuzzy automated matching at this
stage.

## D-010 — 2026-08-30 — Second publisher demonstrates a different observability pattern

**Decision:** Retain the MBTA two-version evaluation as independent evidence
that the current observability chain generalises beyond the Santa Monica case.

**Inputs:**

- official MBTA historical GTFS archive;
- `20260623.zip`;
- `20260624.zip`;
- adjacent archive entries;
- no source-code changes were made for MBTA.

**Observed transition:**

- source ZIP changed;
- no GTFS tables were added or removed;
- the only table row-count change was `calendar_dates.txt`, increasing by one
  row;
- all 403 route IDs persisted;
- no stop IDs were added or removed;
- seven service IDs referenced by trips were added;
- seven service IDs referenced by trips were removed;
- all 403 routes have exact semantic continuity;
- no route continuity ambiguity occurred.

**Interpretation:**

This is materially different from the first Santa Monica evaluation.

Santa Monica exposed near-total route-ID regeneration around largely stable
route semantics. MBTA exposes stable route and stop identities while the
service-calendar identity layer changes beneath an almost unchanged aggregate
table structure.

The same unmodified tooling exposed both patterns.

This provides stronger evidence that the project is measuring genuine
longitudinal GTFS structure rather than encoding publisher-specific behaviour.

The next gate is forensic analysis of the seven removed and seven added MBTA
service IDs. Do not yet infer that service itself was added or removed:
`service_id` is publisher-controlled and may also be regenerated.

## D-011 — 2026-08-30 — MBTA service-ID churn represents changed calendar semantics

**Decision:** Retain service-ID semantic analysis as evidence that identity
changes can represent substantive service-calendar restructuring rather than
identifier regeneration.

**Observed transition:**

Seven service IDs referenced by trips disappear and seven new service IDs
appear between the adjacent MBTA archive versions.

No removed service has:

- an exact semantic match among the added services; or
- an identical effective-date set among the added services.

However, each changed service has a natural added counterpart with the same
route association:

- Green D/E;
- Green B;
- Green C;
- Mattapan;
- Blue;
- Orange;
- Red.

Across all seven cases the pattern is systematic.

Removed services:

- Monday through Thursday weekday mask;
- 40 effective service dates;
- effective span 2026-06-24 through 2026-09-03.

Added services:

- Friday-only weekday mask;
- 12 effective service dates;
- effective span 2026-06-26 through 2026-09-04.

Trip counts also differ between each corresponding route group.

**Interpretation:**

This is not equivalent service represented under regenerated IDs. The service
calendar semantics themselves differ.

The MBTA evaluation therefore demonstrates a second important longitudinal
case:

1. aggregate feed structure is nearly unchanged;
2. route and stop identities remain stable;
3. service IDs churn;
4. semantic inspection shows that the churn corresponds to materially
   different effective service calendars.

The natural route-group correspondence is descriptive evidence of a
relationship between the changed service definitions. It must not be treated
as proof that one service formally replaced another without further evidence.

Do not introduce fuzzy service matching or automated replacement inference at
this stage.
