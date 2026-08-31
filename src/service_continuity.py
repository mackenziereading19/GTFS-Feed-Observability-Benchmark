#!/usr/bin/env python3

import argparse
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    from .gtfs_io import (
        matching_basename_members,
        read_normalized_csv_rows,
    )
except ImportError:
    from gtfs_io import (
        matching_basename_members,
        read_normalized_csv_rows,
    )

try:
    from .service_calendar import (
        WEEKDAYS,
        calculate_active_dates,
        parse_gtfs_date,
    )
except ImportError:
    from service_calendar import (
        WEEKDAYS,
        calculate_active_dates,
        parse_gtfs_date,
    )




def read_table(zf, basename):
    matches = matching_basename_members(
        zf,
        basename,
    )

    if not matches:
        return []

    if len(matches) != 1:
        raise ValueError(
            f"Expected one {basename}; found {len(matches)}"
        )

    return read_normalized_csv_rows(
        zf,
        matches[0],
    )


def parse_date(value):
    return parse_gtfs_date(value)


def load_feed(path):
    with zipfile.ZipFile(path) as zf:
        calendar = read_table(zf, "calendar.txt")
        calendar_dates = read_table(
            zf,
            "calendar_dates.txt",
        )
        trips = read_table(zf, "trips.txt")

    calendar_by_service = {
        row["service_id"]: row
        for row in calendar
    }

    exceptions = defaultdict(list)

    for row in calendar_dates:
        exceptions[row["service_id"]].append(row)

    trips_by_service = defaultdict(list)

    for trip in trips:
        trips_by_service[
            trip["service_id"]
        ].append(trip)

    return {
        "calendar": calendar_by_service,
        "exceptions": exceptions,
        "trips": trips_by_service,
    }


def effective_dates(feed, service_id):
    row = feed["calendar"].get(service_id)

    exceptions = feed["exceptions"].get(
        service_id,
        [],
    )

    calculated = calculate_active_dates(
        row,
        exceptions,
    )

    ordered = calculated["active_dates"]

    return {
        "dates": tuple(
            date.strftime("%Y%m%d")
            for date in ordered
        ),
        "calendar_start": (
            row.get("start_date")
            if row
            else None
        ),
        "calendar_end": (
            row.get("end_date")
            if row
            else None
        ),
        "weekday_mask": (
            tuple(
                row.get(day, "")
                for day in WEEKDAYS
            )
            if row
            else None
        ),
        "exception_additions": (
            calculated[
                "exception_additions"
            ]
        ),
        "exception_removals": (
            calculated[
                "exception_removals"
            ]
        ),
    }


def trip_signature(feed, service_id):
    trips = feed["trips"].get(
        service_id,
        [],
    )

    routes = sorted(
        {
            trip.get("route_id", "")
            for trip in trips
            if trip.get("route_id", "")
        }
    )

    return {
        "trip_count": len(trips),
        "route_ids": routes,
    }


def service_summary(feed, service_id):
    effective = effective_dates(
        feed,
        service_id,
    )

    trip_info = trip_signature(
        feed,
        service_id,
    )

    dates = effective["dates"]

    return {
        "service_id": service_id,
        "calendar_start": effective["calendar_start"],
        "calendar_end": effective["calendar_end"],
        "weekday_mask": list(
            effective["weekday_mask"]
            if effective["weekday_mask"]
            is not None
            else []
        ),
        "exception_additions": list(
            effective["exception_additions"]
        ),
        "exception_removals": list(
            effective["exception_removals"]
        ),
        "effective_date_count": len(dates),
        "effective_first_date": (
            dates[0]
            if dates
            else None
        ),
        "effective_last_date": (
            dates[-1]
            if dates
            else None
        ),
        "effective_dates": list(dates),
        "trip_count": trip_info["trip_count"],
        "route_ids": trip_info["route_ids"],
    }


def semantic_signature(summary):
    return (
        tuple(summary["effective_dates"]),
        tuple(summary["route_ids"]),
        summary["trip_count"],
    )


def date_only_signature(summary):
    return tuple(
        summary["effective_dates"]
    )


def analyse(old_path, new_path):
    old_feed = load_feed(old_path)
    new_feed = load_feed(new_path)

    old_ids = set(old_feed["trips"])
    new_ids = set(new_feed["trips"])

    removed = sorted(old_ids - new_ids)
    added = sorted(new_ids - old_ids)

    old_summaries = {
        sid: service_summary(
            old_feed,
            sid,
        )
        for sid in removed
    }

    new_summaries = {
        sid: service_summary(
            new_feed,
            sid,
        )
        for sid in added
    }

    exact_pairs = []
    date_only_pairs = []

    used_new_exact = set()

    for old_id in removed:
        old_summary = old_summaries[old_id]

        matches = [
            new_id
            for new_id in added
            if semantic_signature(
                old_summary
            )
            == semantic_signature(
                new_summaries[new_id]
            )
        ]

        if len(matches) == 1:
            new_id = matches[0]
            exact_pairs.append(
                {
                    "old_service_id": old_id,
                    "new_service_id": new_id,
                }
            )
            used_new_exact.add(new_id)

    for old_id in removed:
        old_summary = old_summaries[old_id]

        matches = [
            new_id
            for new_id in added
            if date_only_signature(
                old_summary
            )
            == date_only_signature(
                new_summaries[new_id]
            )
        ]

        if len(matches) == 1:
            date_only_pairs.append(
                {
                    "old_service_id": old_id,
                    "new_service_id": matches[0],
                }
            )

    return {
        "schema_version": 1,
        "baseline": Path(old_path).name,
        "candidate": Path(new_path).name,
        "removed_service_ids": removed,
        "added_service_ids": added,
        "removed_services": old_summaries,
        "added_services": new_summaries,
        "exact_semantic_pairs": exact_pairs,
        "date_only_pairs": date_only_pairs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    json.dump(
        analyse(
            args.baseline,
            args.candidate,
        ),
        sys.stdout,
        indent=2,
        sort_keys=True,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
