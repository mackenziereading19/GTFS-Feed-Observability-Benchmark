"""Low-level helpers for reading GTFS tables from ZIP archives."""

import csv
import io


def matching_basename_members(zf, basename):
    """Return non-directory ZIP members matching a basename."""
    return [
        name
        for name in zf.namelist()
        if not name.endswith("/")
        and name.rsplit("/", 1)[-1] == basename
    ]


def read_normalized_csv_rows(zf, member):
    """Read one UTF-8-sig CSV member and strip field values."""
    raw = zf.read(member).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))

    return [
        {
            key: (value or "").strip()
            for key, value in row.items()
        }
        for row in reader
    ]
