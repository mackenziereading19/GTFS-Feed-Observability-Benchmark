#!/usr/bin/env python3

import argparse
import csv
import io
import zipfile
from pathlib import Path


SYNTHETIC_STOP_ID = "__OBSERVABILITY_SYNTHETIC_STOP__"


def read_text(zf, name):
    return zf.read(name).decode("utf-8-sig")


def rewrite_csv(text, transform):
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames

    if not fieldnames:
        raise ValueError("CSV has no header")

    rows = list(reader)
    rows = transform(fieldnames, rows)

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()

    destination.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as src:
        members = {
            name: src.read(name)
            for name in src.namelist()
            if not name.endswith("/")
        }

    # 1. Remove transfers.txt.
    matches = [
        name
        for name in members
        if name.rsplit("/", 1)[-1] == "transfers.txt"
    ]

    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one transfers.txt, found {len(matches)}"
        )

    del members[matches[0]]

    def find_member(basename):
        found = [
            name
            for name in members
            if name.rsplit("/", 1)[-1] == basename
        ]

        if len(found) != 1:
            raise SystemExit(
                f"Expected exactly one {basename}, found {len(found)}"
            )

        return found[0]

    # 2. Add one unused synthetic stop.
    stops_name = find_member("stops.txt")

    def add_stop(fieldnames, rows):
        if any(
            row.get("stop_id") == SYNTHETIC_STOP_ID
            for row in rows
        ):
            raise SystemExit("Synthetic stop already exists")

        row = {field: "" for field in fieldnames}
        row["stop_id"] = SYNTHETIC_STOP_ID

        if "stop_name" in row:
            row["stop_name"] = "Observability synthetic stop"

        if "stop_lat" in row:
            row["stop_lat"] = "-41.2865"

        if "stop_lon" in row:
            row["stop_lon"] = "174.7762"

        if "location_type" in row:
            row["location_type"] = "0"

        rows.append(row)
        return rows

    members[stops_name] = rewrite_csv(
        members[stops_name].decode("utf-8-sig"),
        add_stop,
    )

    # 3. Extend feed_end_date.
    feed_info_name = find_member("feed_info.txt")

    def extend_feed_info(fieldnames, rows):
        if len(rows) != 1:
            raise SystemExit(
                f"Expected one feed_info row, found {len(rows)}"
            )

        actual = rows[0].get("feed_end_date")

        if actual != "20260926":
            raise SystemExit(
                "Unexpected original feed_end_date: "
                f"{actual}"
            )

        rows[0]["feed_end_date"] = "20261003"
        return rows

    members[feed_info_name] = rewrite_csv(
        members[feed_info_name].decode("utf-8-sig"),
        extend_feed_info,
    )

    # 4. Extend one calendar row beyond the original maximum.
    calendar_name = find_member("calendar.txt")

    def extend_calendar(fieldnames, rows):
        if not rows:
            raise SystemExit("calendar.txt has no data rows")

        original_max = max(
            row["end_date"]
            for row in rows
            if row.get("end_date")
        )

        if original_max != "20261031":
            raise SystemExit(
                f"Unexpected calendar max end: {original_max}"
            )

        rows[0]["end_date"] = "20261107"
        return rows

    members[calendar_name] = rewrite_csv(
        members[calendar_name].decode("utf-8-sig"),
        extend_calendar,
    )

    # 5. Add one future calendar_dates exception.
    calendar_dates_name = find_member("calendar_dates.txt")

    def add_calendar_date(fieldnames, rows):
        if not rows:
            raise SystemExit("calendar_dates.txt has no rows")

        original_max = max(
            row["date"]
            for row in rows
            if row.get("date")
        )

        if original_max != "20260926":
            raise SystemExit(
                f"Unexpected exception max date: {original_max}"
            )

        row = {field: "" for field in fieldnames}
        row["service_id"] = rows[0]["service_id"]
        row["date"] = "20261003"
        row["exception_type"] = "1"

        rows.append(row)
        return rows

    members[calendar_dates_name] = rewrite_csv(
        members[calendar_dates_name].decode("utf-8-sig"),
        add_calendar_date,
    )

    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as dst:
        for name in sorted(members):
            info = zipfile.ZipInfo(name)
            # Fixed metadata makes the synthetic ZIP deterministic.
            info.date_time = (2026, 8, 30, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16

            dst.writestr(info, members[name])


if __name__ == "__main__":
    main()
