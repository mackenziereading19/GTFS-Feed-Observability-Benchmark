#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def load_manifest(path):
    with Path(path).open() as handle:
        data = json.load(handle)

    if data.get("schema_version") not in {1, 2}:
        raise ValueError(
            f"Unsupported manifest schema: "
            f"{data.get('schema_version')}"
        )

    return data


def scalar_change(before, after):
    if before == after:
        return None

    return {
        "before": before,
        "after": after,
    }


def numeric_delta(before, after):
    if before is None or after is None:
        return None

    return after - before


def compare_tables(before, after):
    old = before.get("tables", {})
    new = after.get("tables", {})

    old_names = set(old)
    new_names = set(new)

    changed_rows = {}

    for name in sorted(old_names & new_names):
        old_rows = old[name].get("rows")
        new_rows = new[name].get("rows")

        if old_rows != new_rows:
            changed_rows[name] = {
                "before": old_rows,
                "after": new_rows,
                "delta": numeric_delta(
                    old_rows,
                    new_rows,
                ),
            }

    return {
        "added": sorted(new_names - old_names),
        "removed": sorted(old_names - new_names),
        "row_changes": changed_rows,
    }


def compare_entities(before, after):
    old = before.get("entities", {})
    new = after.get("entities", {})

    changes = {}

    keys = sorted(set(old) | set(new))

    for key in keys:
        old_value = old.get(key)
        new_value = new.get(key)

        if old_value == new_value:
            continue

        if (
            isinstance(old_value, dict)
            and isinstance(new_value, dict)
        ):
            fields = {}

            for field in sorted(
                set(old_value) | set(new_value)
            ):
                before_field = old_value.get(field)
                after_field = new_value.get(field)

                if before_field != after_field:
                    item = {
                        "before": before_field,
                        "after": after_field,
                    }

                    if (
                        isinstance(before_field, int)
                        and isinstance(after_field, int)
                    ):
                        item["delta"] = (
                            after_field - before_field
                        )

                    fields[field] = item

            changes[key] = fields
        else:
            item = {
                "before": old_value,
                "after": new_value,
            }

            if (
                isinstance(old_value, int)
                and isinstance(new_value, int)
            ):
                item["delta"] = new_value - old_value

            changes[key] = item

    return changes


def compare_identities(before, after):
    old = before.get("identities", {})
    new = after.get("identities", {})

    changes = {}

    for key in sorted(set(old) | set(new)):
        old_values = set(old.get(key, []))
        new_values = set(new.get(key, []))

        added = sorted(new_values - old_values)
        removed = sorted(old_values - new_values)

        if added or removed:
            changes[key] = {
                "added": added,
                "removed": removed,
            }

    return changes


def first_feed_info(manifest):
    rows = manifest.get("feed_info")

    if not rows:
        return {}

    return rows[0]


def compare_feed_info(before, after):
    old = first_feed_info(before)
    new = first_feed_info(after)

    fields = (
        "feed_publisher_name",
        "feed_publisher_url",
        "feed_lang",
        "feed_start_date",
        "feed_end_date",
        "feed_version",
    )

    changes = {}

    for field in fields:
        change = scalar_change(
            old.get(field),
            new.get(field),
        )

        if change:
            changes[field] = change

    return changes


def get_nested(data, *path):
    current = data

    for part in path:
        if current is None:
            return None

        current = current.get(part)

    return current


def compare_temporal(before, after):
    paths = {
        "calendar.start_date.minimum": (
            "calendar",
            "start_date",
            "minimum",
        ),
        "calendar.start_date.maximum": (
            "calendar",
            "start_date",
            "maximum",
        ),
        "calendar.end_date.minimum": (
            "calendar",
            "end_date",
            "minimum",
        ),
        "calendar.end_date.maximum": (
            "calendar",
            "end_date",
            "maximum",
        ),
        "calendar_dates.date.minimum": (
            "calendar_dates",
            "date",
            "minimum",
        ),
        "calendar_dates.date.maximum": (
            "calendar_dates",
            "date",
            "maximum",
        ),
    }

    changes = {}

    for label, path in paths.items():
        old_value = get_nested(before, *path)
        new_value = get_nested(after, *path)

        change = scalar_change(
            old_value,
            new_value,
        )

        if change:
            changes[label] = change

    return changes


def compare_manifests(before, after):
    return {
        "comparison_schema_version": 1,
        "baseline": {
            "filename": before["source"]["filename"],
            "sha256": before["source"]["sha256"],
        },
        "candidate": {
            "filename": after["source"]["filename"],
            "sha256": after["source"]["sha256"],
        },
        "source_changed": (
            before["source"]["sha256"]
            != after["source"]["sha256"]
        ),
        "tables": compare_tables(
            before,
            after,
        ),
        "entities": compare_entities(
            before,
            after,
        ),
        "identities": compare_identities(
            before,
            after,
        ),
        "feed_info": compare_feed_info(
            before,
            after,
        ),
        "temporal_bounds": compare_temporal(
            before,
            after,
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare two GTFS observability manifests."
        )
    )

    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)

    args = parser.parse_args()

    baseline = load_manifest(args.baseline)
    candidate = load_manifest(args.candidate)

    result = compare_manifests(
        baseline,
        candidate,
    )

    json.dump(
        result,
        sys.stdout,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
