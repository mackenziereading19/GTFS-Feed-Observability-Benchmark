"""Shared GTFS service-calendar primitives."""

from datetime import datetime, timedelta


WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def parse_gtfs_date(value):
    return datetime.strptime(
        value,
        "%Y%m%d",
    ).date()


def calculate_active_dates(calendar, exceptions):
    """Calculate effective service dates without imposing an output schema."""
    active = set()

    if calendar:
        start = parse_gtfs_date(
            calendar["start_date"]
        )
        end = parse_gtfs_date(
            calendar["end_date"]
        )

        current = start

        while current <= end:
            weekday = WEEKDAYS[
                current.weekday()
            ]

            if calendar.get(weekday) == "1":
                active.add(current)

            current += timedelta(days=1)

    additions = []
    removals = []

    for row in exceptions:
        current = parse_gtfs_date(
            row["date"]
        )

        if row["exception_type"] == "1":
            active.add(current)
            additions.append(row["date"])
        elif row["exception_type"] == "2":
            active.discard(current)
            removals.append(row["date"])

    return {
        "active_dates": tuple(sorted(active)),
        "exception_additions": tuple(
            sorted(additions)
        ),
        "exception_removals": tuple(
            sorted(removals)
        ),
    }
