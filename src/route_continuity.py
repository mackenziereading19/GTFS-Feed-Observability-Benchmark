#!/usr/bin/env python3

import argparse
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


CORE_FIELDS = (
    "agency_id",
    "route_short_name",
    "route_long_name",
    "route_type",
)


def find_member(zf, basename):
    matches = [
        name
        for name in zf.namelist()
        if not name.endswith("/")
        and name.rsplit("/", 1)[-1] == basename
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {basename}; found {len(matches)}"
        )

    return matches[0]


def read_routes(path):
    with zipfile.ZipFile(path) as zf:
        member = find_member(zf, "routes.txt")
        raw = zf.read(member).decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(raw))

    if not reader.fieldnames:
        raise ValueError("routes.txt has no header")

    if "route_id" not in reader.fieldnames:
        raise ValueError("routes.txt lacks route_id")

    rows = []

    for row in reader:
        clean = {
            key: (value or "").strip()
            for key, value in row.items()
        }

        if not clean["route_id"]:
            raise ValueError("routes.txt contains blank route_id")

        rows.append(clean)

    return rows, tuple(reader.fieldnames)


def signature(row, fields):
    return tuple(
        (field, row.get(field, ""))
        for field in fields
    )


def full_signature(row, fieldnames):
    fields = sorted(
        field
        for field in fieldnames
        if field != "route_id"
    )

    return signature(row, fields)


def core_signature(row):
    return signature(row, CORE_FIELDS)


def group_by_signature(rows, signature_fn):
    groups = defaultdict(list)

    for row in rows:
        groups[signature_fn(row)].append(row["route_id"])

    for ids in groups.values():
        ids.sort()

    return groups


def classify(old_groups, new_groups):
    matches = []
    ambiguous = []

    common = sorted(
        set(old_groups) & set(new_groups),
        key=repr,
    )

    for sig in common:
        old_ids = old_groups[sig]
        new_ids = new_groups[sig]

        record = {
            "old_ids": old_ids,
            "new_ids": new_ids,
        }

        if len(old_ids) == 1 and len(new_ids) == 1:
            matches.append(record)
        else:
            ambiguous.append(record)

    matched_old = {
        route_id
        for sig in common
        for route_id in old_groups[sig]
    }

    matched_new = {
        route_id
        for sig in common
        for route_id in new_groups[sig]
    }

    all_old = {
        route_id
        for ids in old_groups.values()
        for route_id in ids
    }

    all_new = {
        route_id
        for ids in new_groups.values()
        for route_id in ids
    }

    return {
        "one_to_one": matches,
        "ambiguous": ambiguous,
        "unmatched_old_ids": sorted(all_old - matched_old),
        "unmatched_new_ids": sorted(all_new - matched_new),
    }


def analyse(old_path, new_path):
    old_rows, old_fields = read_routes(old_path)
    new_rows, new_fields = read_routes(new_path)

    all_fields = tuple(
        sorted(
            (set(old_fields) | set(new_fields))
            - {"route_id"}
        )
    )

    old_exact = group_by_signature(
        old_rows,
        lambda row: signature(row, all_fields),
    )

    new_exact = group_by_signature(
        new_rows,
        lambda row: signature(row, all_fields),
    )

    old_core = group_by_signature(
        old_rows,
        core_signature,
    )

    new_core = group_by_signature(
        new_rows,
        core_signature,
    )

    exact = classify(old_exact, new_exact)
    core = classify(old_core, new_core)

    old_ids = sorted(row["route_id"] for row in old_rows)
    new_ids = sorted(row["route_id"] for row in new_rows)

    exact_pairs = [
        {
            "old_route_id": item["old_ids"][0],
            "new_route_id": item["new_ids"][0],
        }
        for item in exact["one_to_one"]
    ]

    core_pairs = [
        {
            "old_route_id": item["old_ids"][0],
            "new_route_id": item["new_ids"][0],
        }
        for item in core["one_to_one"]
    ]

    return {
        "schema_version": 1,
        "baseline": {
            "filename": Path(old_path).name,
            "route_count": len(old_rows),
        },
        "candidate": {
            "filename": Path(new_path).name,
            "route_count": len(new_rows),
        },
        "raw_identity": {
            "persisting_ids": sorted(
                set(old_ids) & set(new_ids)
            ),
            "removed_ids": sorted(
                set(old_ids) - set(new_ids)
            ),
            "added_ids": sorted(
                set(new_ids) - set(old_ids)
            ),
        },
        "exact_semantic_continuity": {
            "definition": (
                "Complete routes.txt row equality excluding route_id."
            ),
            "one_to_one_pairs": exact_pairs,
            "ambiguous_groups": exact["ambiguous"],
            "unmatched_old_ids": exact["unmatched_old_ids"],
            "unmatched_new_ids": exact["unmatched_new_ids"],
        },
        "core_continuity": {
            "definition": (
                "Exact equality of agency_id, route_short_name, "
                "route_long_name and route_type."
            ),
            "fields": list(CORE_FIELDS),
            "one_to_one_pairs": core_pairs,
            "ambiguous_groups": core["ambiguous"],
            "unmatched_old_ids": core["unmatched_old_ids"],
            "unmatched_new_ids": core["unmatched_new_ids"],
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyse semantic continuity of routes across two GTFS feeds."
        )
    )

    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)

    args = parser.parse_args()

    result = analyse(
        args.baseline,
        args.candidate,
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
