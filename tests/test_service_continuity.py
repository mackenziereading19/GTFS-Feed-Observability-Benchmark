import tempfile
import unittest
import zipfile
from pathlib import Path

from src.service_continuity import (
    analyse,
    effective_dates,
    load_feed,
)


def write_zip(path, files):
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for name, content in sorted(files.items()):
            zf.writestr(name, content)


def feed_files(
    service_id,
    weekday_mask,
    start_date,
    end_date,
    calendar_dates="",
):
    monday, tuesday, wednesday, thursday, friday, saturday, sunday = (
        weekday_mask
    )

    return {
        "calendar.txt": (
            "service_id,monday,tuesday,wednesday,"
            "thursday,friday,saturday,sunday,"
            "start_date,end_date\n"
            f"{service_id},"
            f"{monday},{tuesday},{wednesday},"
            f"{thursday},{friday},{saturday},{sunday},"
            f"{start_date},{end_date}\n"
        ),
        "calendar_dates.txt": (
            "service_id,date,exception_type\n"
            + calendar_dates
        ),
        "trips.txt": (
            "route_id,service_id,trip_id\n"
            f"R1,{service_id},T1\n"
            f"R1,{service_id},T2\n"
        ),
    }


class ServiceContinuityTest(unittest.TestCase):
    def test_effective_dates_apply_additions_and_removals(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed = Path(tmp) / "feed.zip"

            files = feed_files(
                service_id="OLD",
                weekday_mask=(
                    "1", "1", "1", "1", "1", "0", "0"
                ),
                start_date="20260824",
                end_date="20260830",
                calendar_dates=(
                    "OLD,20260825,2\n"
                    "OLD,20260829,1\n"
                ),
            )

            write_zip(feed, files)

            loaded = load_feed(feed)
            result = effective_dates(
                loaded,
                "OLD",
            )

            self.assertEqual(
                result["dates"],
                (
                    "20260824",
                    "20260826",
                    "20260827",
                    "20260828",
                    "20260829",
                ),
            )

    def test_exact_semantic_service_id_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.zip"
            new = Path(tmp) / "new.zip"

            common = {
                "weekday_mask": (
                    "1", "1", "1", "1", "1", "0", "0"
                ),
                "start_date": "20260824",
                "end_date": "20260828",
            }

            write_zip(
                old,
                feed_files(
                    "OLD",
                    **common,
                ),
            )

            write_zip(
                new,
                feed_files(
                    "NEW",
                    **common,
                ),
            )

            result = analyse(old, new)

            self.assertEqual(
                result["exact_semantic_pairs"],
                [
                    {
                        "old_service_id": "OLD",
                        "new_service_id": "NEW",
                    }
                ],
            )

            self.assertEqual(
                result["date_only_pairs"],
                [
                    {
                        "old_service_id": "OLD",
                        "new_service_id": "NEW",
                    }
                ],
            )

    def test_changed_calendar_is_not_exact_continuity(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "old.zip"
            new = Path(tmp) / "new.zip"

            write_zip(
                old,
                feed_files(
                    "OLD",
                    (
                        "1", "1", "1", "1",
                        "0", "0", "0",
                    ),
                    "20260824",
                    "20260903",
                ),
            )

            write_zip(
                new,
                feed_files(
                    "NEW",
                    (
                        "0", "0", "0", "0",
                        "1", "0", "0",
                    ),
                    "20260824",
                    "20260904",
                ),
            )

            result = analyse(old, new)

            self.assertEqual(
                result["exact_semantic_pairs"],
                [],
            )

            self.assertEqual(
                result["date_only_pairs"],
                [],
            )


if __name__ == "__main__":
    unittest.main()
