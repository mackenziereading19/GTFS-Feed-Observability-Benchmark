
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
