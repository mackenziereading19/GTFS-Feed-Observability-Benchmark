import tempfile
import unittest
import zipfile
from pathlib import Path

from src.route_forensics import (
    effective_service_dates,
    load_feed,
    route_summary,
)


def write_zip(path, files):
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for name, content in sorted(files.items()):
            zf.writestr(name, content)


class RouteForensicsTest(unittest.TestCase):
    def fixture(self):
        return {
            "routes.txt": (
                "route_id,agency_id,route_short_name,"
                "route_long_name,route_type\n"
                "3075,A,20,Example Shuttle,3\n"
            ),
            "trips.txt": (
                "route_id,service_id,trip_id,"
                "trip_headsign,direction_id\n"
                "3075,SVC,T1,Outbound,0\n"
                "3075,SVC,T2,Inbound,1\n"
            ),
            "stop_times.txt": (
                "trip_id,arrival_time,departure_time,"
                "stop_id,stop_sequence\n"
                "T1,08:00:00,08:00:00,A,1\n"
                "T1,08:10:00,08:10:00,B,2\n"
                "T2,09:00:00,09:00:00,B,1\n"
                "T2,09:10:00,09:10:00,A,2\n"
            ),
            "calendar.txt": (
                "service_id,monday,tuesday,wednesday,"
                "thursday,friday,saturday,sunday,"
                "start_date,end_date\n"
                "SVC,0,0,0,0,0,0,0,"
                "20260801,20260831\n"
            ),
            "calendar_dates.txt": (
                "service_id,date,exception_type\n"
                "SVC,20260819,1\n"
                "SVC,20260820,1\n"
                "SVC,20260821,1\n"
            ),
        }

    def test_exception_only_service_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_path = Path(tmp) / "feed.zip"
            write_zip(
                feed_path,
                self.fixture(),
            )

            feed = load_feed(feed_path)

            service = effective_service_dates(
                feed,
                "SVC",
            )

            self.assertEqual(
                service["active_weekdays"],
                [],
            )
            self.assertEqual(
                service["effective_date_count"],
                3,
            )
            self.assertEqual(
                service["effective_first_date"],
                "2026-08-19",
            )
            self.assertEqual(
                service["effective_last_date"],
                "2026-08-21",
            )

    def test_route_summary_preserves_service_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_path = Path(tmp) / "feed.zip"
            write_zip(
                feed_path,
                self.fixture(),
            )

            feed = load_feed(feed_path)
            summary = route_summary(
                feed,
                "3075",
            )

            self.assertEqual(
                summary["trip_count"],
                2,
            )
            self.assertEqual(
                summary["service_ids"],
                ["SVC"],
            )
            self.assertEqual(
                summary["direction_ids"],
                ["0", "1"],
            )
            self.assertEqual(
                summary["trip_headsigns"],
                ["Inbound", "Outbound"],
            )
            self.assertEqual(
                summary["unique_stop_patterns"],
                2,
            )

            self.assertEqual(
                summary["effective_service_span"],
                {
                    "first_date": "2026-08-19",
                    "last_date": "2026-08-21",
                },
            )


if __name__ == "__main__":
    unittest.main()
