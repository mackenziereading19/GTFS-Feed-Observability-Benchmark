# GTFS Feed Observability Benchmark

A reproducible, feed-version-oriented toolkit for observing how GTFS Schedule
datasets change over time.

## Problem

GTFS validation answers whether a particular feed contains specification,
best-practice or data-quality problems at a point in time.

Operational feed monitoring asks a different set of questions:

- Has the feed changed since the previous publication?
- Has its service horizon shortened?
- Have routes, trips, stops or service definitions disappeared?
- Is the publisher repeatedly issuing materially identical feeds?
- Has structural churn occurred between versions?
- Are changes routine publication behaviour or potentially significant?

Existing tools provide useful validation, pairwise diffing and GTFS querying,
but this project investigates whether a small reproducible observability layer
can preserve longitudinal feed evidence without introducing new validation
rules.

## Feasibility-first boundary

This project does not assume that a complete observability product is needed.

Development proceeds in bounded stages:

1. deterministic snapshot manifest;
2. deterministic comparison between two manifests;
3. service-horizon metrics;
4. structural-change metrics;
5. repeated-version evidence;
6. evaluation against real feed histories;
7. only then decide whether a reusable tool is justified.

A negative result is acceptable.

## V0

V0 takes a local GTFS ZIP and emits a deterministic JSON manifest containing:

- source filename;
- ZIP SHA-256;
- archive byte size;
- GTFS table inventory;
- row counts;
- selected entity counts;
- `feed_info.txt` metadata when present;
- raw `calendar.txt` date bounds;
- raw `calendar_dates.txt` exception-date bounds;
- service-ID counts.

It intentionally does **not** calculate a health score or infer problems.

## Requirements

Python 3.11+ recommended.

V0 uses only the Python standard library.

## Usage

```bash
python3 src/gtfs_observe.py FEED.zip > manifest.json

```

## V1 — Pairwise manifest comparison

V1 compares two snapshot manifests and reports descriptive changes including:

- whether the source ZIP hash changed;
- tables added or removed;
- GTFS table row-count deltas;
- selected entity-count deltas;
- selected `feed_info.txt` changes;
- raw calendar and exception-date boundary changes.

V1 remains descriptive. It does not label changes as healthy, unhealthy,
anomalous or erroneous.

Usage:

```bash
python3 src/gtfs_compare.py \
  baseline-manifest.json \
  candidate-manifest.json

```

## Unified command-line interface

The repository also provides one additive command-line entry point:

```bash
python3 -m src.cli --help
```

Available subcommands:

```text
observe
compare
route-continuity
route-forensics
service-continuity
```

Examples:

```bash
python3 -m src.cli observe FEED.zip > manifest.json

python3 -m src.cli compare baseline-manifest.json candidate-manifest.json

python3 -m src.cli route-continuity baseline.zip candidate.zip

python3 -m src.cli route-forensics baseline.zip candidate.zip

python3 -m src.cli service-continuity baseline.zip candidate.zip
```

Run any subcommand with `--help` for its argument contract.

The unified CLI is additive. The existing script entry points remain
supported and preserve their previous behaviour.

`route-forensics` is a bounded forensic tool developed around the frozen
route targets used in the repository evidence. It should not be interpreted
as a generic route-matching command without first reviewing its configured
targets and assumptions.

## V3 — Identity-aware change

Manifest schema 2 optionally preserves sorted identity sets for:

- routes;
- stops;
- service IDs referenced by trips.

Pairwise comparison can therefore report identifiers added and removed between
feed versions.

Identity disappearance is descriptive evidence only. A removed GTFS ID does
not establish that the corresponding real-world service or infrastructure was
removed because publishers may regenerate identifiers between feed versions.

Schema-1 manifests remain readable by the comparator.

## V4 — Route semantic continuity

Route continuity analysis distinguishes identifier churn from apparent
route-definition continuity.

Two conservative signatures are supported:

- exact equality of the complete `routes.txt` row except `route_id`;
- exact equality of `agency_id`, `route_short_name`, `route_long_name` and
  `route_type`.

The analysis does not use fuzzy matching and does not interpret unmatched
routes as withdrawn services.

In the first real historical evaluation, 20 of 22 old Santa Monica route IDs
mapped one-to-one to semantically identical new routes despite no route IDs
persisting between feed versions.

## V5 — Unmatched-route forensics

When a route has no conservative semantic successor, forensic analysis can
inspect:

- route metadata;
- trip counts;
- service IDs;
- effective service dates after `calendar_dates.txt` exceptions;
- trip headsigns;
- stop patterns;
- descriptive candidate overlap in the succeeding feed.

Candidate ranking is investigative only and is not used as an automated fuzzy
continuity rule.

The first real evaluation found that both unmatched Santa Monica routes were
exception-only services whose effective service periods were much shorter than
their nominal `calendar.txt` bounds.

## Second-publisher evaluation — MBTA

The observability chain was evaluated unchanged against two adjacent official
MBTA historical GTFS archive versions.

Unlike the first Santa Monica evaluation, MBTA showed complete route identity
and semantic continuity:

- 403/403 route IDs persisted;
- no route IDs were added or removed;
- no stop IDs were added or removed;
- all 403 routes matched exactly across versions.

At the same time, seven trip-referenced service IDs were added and seven were
removed even though the only aggregate table row-count change was a single
additional `calendar_dates.txt` row.

This demonstrates that different GTFS publishers can expose materially
different longitudinal patterns through the same descriptive observability
model.

## Service-calendar continuity

Service-ID comparison can distinguish pure identifier regeneration from
changes in effective service semantics.

In the MBTA evaluation, seven removed and seven added service IDs had no exact
semantic or effective-date matches.

The changed IDs nevertheless formed seven natural route-group relationships.
Across every case, the removed service represented Monday–Thursday operation
while the added service represented Friday-only operation.

This shows that a nearly unchanged aggregate GTFS snapshot can conceal
substantive restructuring at the service-calendar layer.

## Testing

The test suite uses Python `unittest` and requires no third-party packages.

Run all tests from the repository root:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

The tests create their own temporary GTFS fixtures where ZIP inputs are required. They do not depend on the ignored local `tmp/` directory or on the real-world source ZIPs used during exploratory evaluation.

## Reproducibility and provenance

Tracked JSON files under `evidence/` preserve outputs from the longitudinal evaluations used during development.

Source provenance for the real-world evaluations is recorded in:

 - `evidence/santa-monica/SOURCE_PROVENANCE.txt`;
 - `evidence/mbta/SOURCE_PROVENANCE.txt`.

The original GTFS ZIP files are not committed to this repository. Local ZIP inputs and exploratory working files are intentionally excluded by `.gitignore`.

The tracked evidence therefore records the derived outputs and source provenance, while reproduction from the original publisher archives requires obtaining the corresponding source feeds described by the provenance records.

Synthetic regression tests are self-contained and can be run from a fresh clone without those real-world source archives.

## Limitations

This toolkit is descriptive observability software, not a GTFS validator and not a service-health scoring system.

A detected change does not by itself establish an error, deterioration, withdrawal of service, or real-world infrastructure change. GTFS identifiers may be regenerated between feed versions, so identifier disappearance should not be treated as proof that the represented service or object disappeared.

`route-forensics` is intentionally bounded to the frozen route targets used in the repository evidence. It is retained as a reproducible forensic tool, not presented as a general-purpose route matcher.

The repository does not currently provide a hosted service, database, publisher identity resolution, fuzzy authoritative matching, or automatic interpretation of operational intent.

## License

The software in this repository is released under the MIT License. See `LICENSE`.
