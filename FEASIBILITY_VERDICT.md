# GTFS Feed Observability Benchmark — Feasibility Verdict

**Date:** 2026-08-30

**Verdict:** GO

## Question

Is there evidence for a useful, reproducible GTFS longitudinal observability
capability that is distinct from ordinary validation and raw file diffing?

## Answer

Yes.

The feasibility investigation has demonstrated, across two independent GTFS
publishers, that deterministic longitudinal comparison can expose meaningful
differences between aggregate change, identifier churn and semantic change.

The evidence supports continuing the project as a bounded reusable tool.

## Demonstrated capability

The current implementation can:

1. create deterministic snapshot manifests from GTFS ZIP files;
2. compare aggregate table and entity structure between feed versions;
3. preserve and compare selected GTFS identities;
4. distinguish raw route-ID churn from conservative semantic route continuity;
5. inspect unmatched route cases using route, trip, stop-pattern and effective
   service-date evidence;
6. distinguish service-ID regeneration hypotheses from actual changes in
   effective service-calendar semantics.

Outputs are deterministic and source inputs are provenance-frozen.

## Real-world evidence

### City of Santa Monica / Big Blue Bus

Two genuine historical publisher archive versions were evaluated.

At the aggregate level:

- routes changed from 22 to 20;
- trips changed from 3,720 to 3,563;
- stops changed from 924 to 923.

Raw identity comparison showed:

- 22 route IDs removed;
- 20 route IDs added;
- zero route IDs persisted.

Semantic continuity analysis then showed:

- 20 one-to-one exact route matches when `route_id` was excluded;
- 20/22 old routes had exact semantic continuity;
- 20/20 new routes had exact semantic predecessors;
- no ambiguous route groups;
- only two old routes remained unmatched.

Those two unmatched routes were then shown to be bounded exception-only
services:

- Route 20 / `route_id=3075`:
  - five effective service dates;
  - 2019-08-19 through 2019-08-23;
  - no regular weekday service.

- Route 45 / `route_id=3082`:
  - effective span 2019-08-18 through 2019-09-01;
  - no regular weekday service;
  - service represented entirely through exception-based calendar activity.

This demonstrates that raw route-ID churn substantially overstated underlying
route-definition change.

### Massachusetts Bay Transportation Authority

Two adjacent official MBTA historical archive versions were evaluated without
changing the source code.

The feed showed:

- no tables added or removed;
- only one aggregate row-count change:
  `calendar_dates.txt` increased by one row;
- all 403 route IDs persisted;
- all 403 routes had exact semantic continuity;
- no stop IDs changed.

Despite that apparent stability:

- seven trip-referenced service IDs were removed;
- seven were added.

Service semantic analysis showed:

- zero exact semantic service matches;
- zero effective-date-only matches;
- each changed service had a natural counterpart serving the same route group;
- removed services represented Monday–Thursday operation with 40 effective
  dates;
- added services represented Friday-only operation with 12 effective dates.

This demonstrates substantive calendar-level change beneath an almost
unchanged aggregate feed structure.

## Why this is distinct from ordinary diffing

A raw file or row-count diff can identify that values changed, but it does not
by itself distinguish:

- identifier regeneration from underlying semantic change;
- nominal calendar bounds from effective service dates after exceptions;
- route-ID disappearance from actual absence of a semantic successor;
- nearly unchanged aggregate files from substantive service-calendar changes.

The project has demonstrated each of these distinctions on real publisher
histories.

## Generalisability

The same implementation produced useful evidence for two publishers with
opposite longitudinal patterns:

- Santa Monica: extensive route-ID churn with high semantic continuity;
- MBTA: completely stable route identities but meaningful service-calendar
  restructuring.

No MBTA-specific source-code changes were required.

This is sufficient feasibility evidence to justify a reusable-tool phase.

## Boundaries

The project must remain descriptive unless stronger evidence supports further
interpretation.

It must not currently:

- infer that a removed identifier means a real-world service was withdrawn;
- infer formal replacement relationships solely from shared route association;
- use fuzzy matching as an authoritative continuity mechanism;
- generate arbitrary feed-health scores;
- label changes as anomalous or erroneous without an external basis;
- duplicate GTFS validator rules.

## Feasibility conclusion

**GO.**

The exploratory phase has established a real and reproducible longitudinal
observability problem and demonstrated a useful technical approach.

Further exploratory feature accumulation should stop here.

The next phase should concentrate on turning the demonstrated capabilities
into a coherent reusable tool through:

1. interface consolidation;
2. stronger automated testing;
3. explicit schemas and compatibility guarantees;
4. concise user documentation;
5. packaging and command-line ergonomics;
6. additional publisher evaluation as acceptance testing rather than
   feature discovery.

The evidence does not justify health scoring, fuzzy automated semantic
matching or service-withdrawal inference.

## Frozen exploratory endpoint

Repository exploratory endpoint:

`887adf87f656f5254dd3124a49d491f851e27b1e`

This commit represents the end of feasibility-driven feature development.
