#!/usr/bin/env python3

import argparse
import csv
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

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


TARGETS = {"3075", "3082"}


def find_member(zf, basename):
    matches = [
        name
        for name in zf.namelist()
        if not name.endswith("/")
        and name.rsplit("/", 1)[-1] == basename
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one {basename}; found {len(matches)}"
        )

    return matches[0]


def read_table(zf, basename):
    member = find_member(zf, basename)
    raw = zf.read(member).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))

    return [
        {
            k: (v or "").strip()
            for k, v in row.items()
        }
        for row in reader
    ]


def load_feed(path):
    with zipfile.ZipFile(path) as zf:
        routes = read_table(zf, "routes.txt")
        trips = read_table(zf, "trips.txt")
        stop_times = read_table(zf, "stop_times.txt")
        calendar = read_table(zf, "calendar.txt")
        calendar_dates = read_table(
            zf,
            "calendar_dates.txt",
        )

    trips_by_route = defaultdict(list)

    for trip in trips:
        trips_by_route[trip["route_id"]].append(trip)

    stop_times_by_trip = defaultdict(list)

    for row in stop_times:
        stop_times_by_trip[row["trip_id"]].append(row)

    for rows in stop_times_by_trip.values():
        rows.sort(
            key=lambda r: int(r.get("stop_sequence") or 0)
        )

    calendar_by_service = {
        row["service_id"]: row
        for row in calendar
    }

    exceptions_by_service = defaultdict(list)

    for row in calendar_dates:
        exceptions_by_service[
            row["service_id"]
        ].append(row)

    return {
        "routes": {
            row["route_id"]: row
            for row in routes
        },
        "trips_by_route": trips_by_route,
        "stop_times_by_trip": stop_times_by_trip,
        "calendar_by_service": calendar_by_service,
        "exceptions_by_service": exceptions_by_service,
    }




def parse_date(value):
    return parse_gtfs_date(value)


def effective_service_dates(feed, service_id):
    calendar = feed[
        "calendar_by_service"
    ].get(service_id)

    exceptions = feed[
        "exceptions_by_service"
    ].get(service_id, [])

    calculated = calculate_active_dates(
        calendar,
        exceptions,
    )

    ordered = calculated["active_dates"]

    return {
        "calendar_start_date": (
            calendar.get("start_date")
            if calendar
            else None
        ),
        "calendar_end_date": (
            calendar.get("end_date")
            if calendar
            else None
        ),
        "active_weekdays": (
            [
                day
                for day in WEEKDAYS
                if calendar.get(day) == "1"
            ]
            if calendar
            else []
        ),
        "exception_additions": list(
            calculated[
                "exception_additions"
            ]
        ),
        "exception_removals": list(
            calculated[
                "exception_removals"
            ]
        ),
        "effective_date_count": len(ordered),
        "effective_first_date": (
            ordered[0].isoformat()
            if ordered
            else None
        ),
        "effective_last_date": (
            ordered[-1].isoformat()
            if ordered
            else None
        ),
    }


def route_summary(feed, route_id):
    route = feed["routes"].get(route_id)

    if route is None:
        return None

    trips = feed["trips_by_route"].get(route_id, [])

    service_ids = sorted(
        {
            trip.get("service_id", "")
            for trip in trips
            if trip.get("service_id", "")
        }
    )

    directions = sorted(
        {
            trip.get("direction_id", "")
            for trip in trips
            if trip.get("direction_id", "") != ""
        }
    )

    heads = sorted(
        {
            trip.get("trip_headsign", "")
            for trip in trips
            if trip.get("trip_headsign", "")
        }
    )

    stop_sequences = Counter()

    for trip in trips:
        rows = feed["stop_times_by_trip"].get(
            trip["trip_id"],
            [],
        )

        sequence = tuple(
            row.get("stop_id", "")
            for row in rows
        )

        if sequence:
            stop_sequences[sequence] += 1

    top_sequences = [
        {
            "trip_count": count,
            "stop_ids": list(sequence),
        }
        for sequence, count in stop_sequences.most_common(10)
    ]

    service_calendars = {
        service_id: effective_service_dates(
            feed,
            service_id,
        )
        for service_id in service_ids
    }

    all_effective_dates = []

    for service in service_calendars.values():
        if service["effective_first_date"]:
            all_effective_dates.append(
                service["effective_first_date"]
            )

        if service["effective_last_date"]:
            all_effective_dates.append(
                service["effective_last_date"]
            )

    return {
        "route": route,
        "trip_count": len(trips),
        "service_ids": service_ids,
        "service_calendars": service_calendars,
        "effective_service_span": {
            "first_date": (
                min(all_effective_dates)
                if all_effective_dates
                else None
            ),
            "last_date": (
                max(all_effective_dates)
                if all_effective_dates
                else None
            ),
        },
        "direction_ids": directions,
        "trip_headsigns": heads,
        "unique_stop_patterns": len(stop_sequences),
        "top_stop_patterns": top_sequences,
    }


def text_similarity_fields(old_route, new_route):
    fields = (
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_type",
        "route_desc",
        "route_url",
        "route_color",
        "route_text_color",
    )

    equal = []
    different = {}

    for field in fields:
        old = old_route.get(field, "")
        new = new_route.get(field, "")

        if old == new:
            equal.append(field)
        else:
            different[field] = {
                "old": old,
                "new": new,
            }

    return {
        "equal_fields": equal,
        "different_fields": different,
    }


def stop_set(summary):
    result = set()

    for pattern in summary["top_stop_patterns"]:
        result.update(pattern["stop_ids"])

    return result


def candidate_scores(old_summary, new_feed):
    old_route = old_summary["route"]
    old_stops = stop_set(old_summary)

    candidates = []

    for route_id in sorted(new_feed["routes"]):
        summary = route_summary(new_feed, route_id)
        route = summary["route"]

        comparison = text_similarity_fields(
            old_route,
            route,
        )

        new_stops = stop_set(summary)

        union = old_stops | new_stops
        intersection = old_stops & new_stops

        stop_jaccard = (
            len(intersection) / len(union)
            if union
            else 0.0
        )

        exact_short_name = (
            old_route.get("route_short_name", "")
            == route.get("route_short_name", "")
        )

        exact_long_name = (
            old_route.get("route_long_name", "")
            == route.get("route_long_name", "")
        )

        exact_type = (
            old_route.get("route_type", "")
            == route.get("route_type", "")
        )

        candidates.append(
            {
                "route_id": route_id,
                "route_short_name": route.get(
                    "route_short_name",
                    "",
                ),
                "route_long_name": route.get(
                    "route_long_name",
                    "",
                ),
                "route_type": route.get(
                    "route_type",
                    "",
                ),
                "trip_count": summary["trip_count"],
                "exact_short_name": exact_short_name,
                "exact_long_name": exact_long_name,
                "exact_route_type": exact_type,
                "equal_route_fields": len(
                    comparison["equal_fields"]
                ),
                "different_route_fields": (
                    comparison["different_fields"]
                ),
                "stop_set_jaccard": round(
                    stop_jaccard,
                    6,
                ),
            }
        )

    candidates.sort(
        key=lambda x: (
            x["exact_short_name"],
            x["exact_long_name"],
            x["exact_route_type"],
            x["stop_set_jaccard"],
            x["equal_route_fields"],
        ),
        reverse=True,
    )

    return candidates[:10]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    old_feed = load_feed(args.baseline)
    new_feed = load_feed(args.candidate)

    result = {
        "schema_version": 1,
        "baseline": args.baseline.name,
        "candidate": args.candidate.name,
        "targets": {},
    }

    for route_id in sorted(TARGETS):
        old_summary = route_summary(
            old_feed,
            route_id,
        )

        if old_summary is None:
            raise ValueError(
                f"Target route {route_id} absent from baseline"
            )

        result["targets"][route_id] = {
            "baseline_summary": old_summary,
            "candidate_matches": candidate_scores(
                old_summary,
                new_feed,
            ),
        }

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
