#!/usr/bin/env python3

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def normalise_name(name: str) -> str:
    return name.rsplit("/", 1)[-1]


def decode_csv(raw: bytes) -> str:
    return raw.decode("utf-8-sig")


def read_rows(zf: zipfile.ZipFile, member: str):
    raw = zf.read(member)
    text = decode_csv(raw)

    reader = csv.DictReader(io.StringIO(text))

    return list(reader), reader.fieldnames or []


def count_data_rows(raw: bytes) -> int:
    text = decode_csv(raw)
    reader = csv.reader(io.StringIO(text))

    try:
        next(reader)
    except StopIteration:
        return 0

    return sum(1 for _ in reader)


def date_bounds(rows, field):
    values = sorted(
        {
            row.get(field, "").strip()
            for row in rows
            if row.get(field, "").strip()
        }
    )

    return {
        "minimum": values[0] if values else None,
        "maximum": values[-1] if values else None,
    }


def unique_count(rows, field):
    return len(
        {
            row.get(field, "").strip()
            for row in rows
            if row.get(field, "").strip()
        }
    )


def main():
    parser = argparse.ArgumentParser(
        description="Create a deterministic GTFS snapshot manifest."
    )

    parser.add_argument(
        "feed",
        type=Path,
        help="Path to a local GTFS ZIP.",
    )

    args = parser.parse_args()

    feed = args.feed.expanduser().resolve()

    if not feed.is_file():
        raise SystemExit(f"Feed does not exist: {feed}")

    manifest = {
        "schema_version": 1,
        "source": {
            "filename": feed.name,
            "sha256": sha256_file(feed),
            "size_bytes": feed.stat().st_size,
        },
        "archive": {},
        "tables": {},
        "entities": {},
        "feed_info": None,
        "calendar": None,
        "calendar_dates": None,
    }

    with zipfile.ZipFile(feed) as zf:
        members = [
            name
            for name in zf.namelist()
            if not name.endswith("/")
        ]

        basename_to_member = {}

        for member in members:
            basename = normalise_name(member)

            if basename in basename_to_member:
                raise SystemExit(
                    "Ambiguous archive: multiple members named "
                    f"{basename}"
                )

            basename_to_member[basename] = member

        manifest["archive"] = {
            "file_count": len(members),
            "filenames": sorted(basename_to_member),
        }

        for table in sorted(basename_to_member):
            member = basename_to_member[table]
            raw = zf.read(member)

            entry = {
                "size_bytes": len(raw),
            }

            if table.endswith(".txt"):
                try:
                    entry["rows"] = count_data_rows(raw)
                except UnicodeDecodeError:
                    entry["rows"] = None

            manifest["tables"][table] = entry

        cache = {}

        def rows_for(table):
            if table not in basename_to_member:
                return [], []

            if table not in cache:
                cache[table] = read_rows(
                    zf,
                    basename_to_member[table],
                )

            return cache[table]

        entity_fields = {
            "agency.txt": ("agencies", "agency_id"),
            "stops.txt": ("stops", "stop_id"),
            "routes.txt": ("routes", "route_id"),
            "trips.txt": ("trips", "trip_id"),
        }

        for table, (label, identifier) in entity_fields.items():
            rows, _ = rows_for(table)

            if rows:
                manifest["entities"][label] = {
                    "rows": len(rows),
                    "unique_ids": unique_count(
                        rows,
                        identifier,
                    ),
                }

        trips, _ = rows_for("trips.txt")

        if trips:
            manifest["entities"]["service_ids_in_trips"] = unique_count(
                trips,
                "service_id",
            )

        calendar, _ = rows_for("calendar.txt")

        if calendar:
            manifest["calendar"] = {
                "rows": len(calendar),
                "service_ids": unique_count(
                    calendar,
                    "service_id",
                ),
                "start_date": date_bounds(
                    calendar,
                    "start_date",
                ),
                "end_date": date_bounds(
                    calendar,
                    "end_date",
                ),
            }

        calendar_dates, _ = rows_for("calendar_dates.txt")

        if calendar_dates:
            manifest["calendar_dates"] = {
                "rows": len(calendar_dates),
                "service_ids": unique_count(
                    calendar_dates,
                    "service_id",
                ),
                "date": date_bounds(
                    calendar_dates,
                    "date",
                ),
                "exception_types": sorted(
                    {
                        row.get("exception_type", "").strip()
                        for row in calendar_dates
                        if row.get("exception_type", "").strip()
                    }
                ),
            }

        feed_info, _ = rows_for("feed_info.txt")

        if feed_info:
            manifest["feed_info"] = [
                {
                    key: value
                    for key, value in sorted(row.items())
                }
                for row in feed_info
            ]

    json.dump(
        manifest,
        sys.stdout,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )

    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
