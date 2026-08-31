import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "gtfs_observe.py"


def write_zip(path, files):
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for name, content in sorted(files.items()):
            zf.writestr(name, content)


class GtfsObserveTest(unittest.TestCase):
    def run_observe(self, feed):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(feed),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        return json.loads(result.stdout), result.stdout

    def fixture_files(self):
        return {
            "agency.txt": (
                "agency_id,agency_name,agency_url,"
                "agency_timezone\n"
                "A,Example Transit,"
                "https://example.test,Europe/London\n"
            ),
            "routes.txt": (
                "route_id,agency_id,route_short_name,"
                "route_long_name,route_type\n"
                "R1,A,1,Example Route,3\n"
            ),
            "stops.txt": (
                "stop_id,stop_name,stop_lat,stop_lon\n"
                "S1,One,51.0,-1.0\n"
                "S2,Two,51.1,-1.1\n"
            ),
            "trips.txt": (
                "route_id,service_id,trip_id\n"
                "R1,WK,T1\n"
                "R1,WK,T2\n"
            ),
            "stop_times.txt": (
                "trip_id,arrival_time,departure_time,"
                "stop_id,stop_sequence\n"
                "T1,08:00:00,08:00:00,S1,1\n"
                "T1,08:10:00,08:10:00,S2,2\n"
                "T2,09:00:00,09:00:00,S1,1\n"
                "T2,09:10:00,09:10:00,S2,2\n"
            ),
            "calendar.txt": (
                "service_id,monday,tuesday,wednesday,"
                "thursday,friday,saturday,sunday,"
                "start_date,end_date\n"
                "WK,1,1,1,1,1,0,0,"
                "20260824,20260904\n"
            ),
            "calendar_dates.txt": (
                "service_id,date,exception_type\n"
                "WK,20260831,2\n"
                "WK,20260905,1\n"
            ),
            "feed_info.txt": (
                "feed_publisher_name,feed_publisher_url,"
                "feed_lang,feed_start_date,feed_end_date,"
                "feed_version\n"
                "Example,https://example.test,en,"
                "20260824,20260905,v1\n"
            ),
        }

    def test_manifest_schema_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed = Path(tmp) / "feed.zip"
            write_zip(feed, self.fixture_files())

            manifest, _ = self.run_observe(feed)

            self.assertEqual(
                manifest["schema_version"],
                2,
            )

            self.assertEqual(
                manifest["tables"]["agency.txt"]["rows"],
                1,
            )
            self.assertEqual(
                manifest["tables"]["routes.txt"]["rows"],
                1,
            )
            self.assertEqual(
                manifest["tables"]["stops.txt"]["rows"],
                2,
            )
            self.assertEqual(
                manifest["tables"]["trips.txt"]["rows"],
                2,
            )
            self.assertEqual(
                manifest["tables"]["stop_times.txt"]["rows"],
                4,
            )

            self.assertEqual(
                manifest["entities"]["routes"]["unique_ids"],
                1,
            )
            self.assertEqual(
                manifest["entities"]["stops"]["unique_ids"],
                2,
            )
            self.assertEqual(
                manifest["entities"]["trips"]["unique_ids"],
                2,
            )

    def test_identity_lists_are_deterministic(self):
        files = self.fixture_files()

        files["stops.txt"] = (
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "S2,Two,51.1,-1.1\n"
            "S1,One,51.0,-1.0\n"
        )

        with tempfile.TemporaryDirectory() as tmp:
            feed = Path(tmp) / "feed.zip"
            write_zip(feed, files)

            first, first_raw = self.run_observe(feed)
            second, second_raw = self.run_observe(feed)

            self.assertEqual(first_raw, second_raw)

            self.assertEqual(
                first["identities"]["stops"],
                ["S1", "S2"],
            )
            self.assertEqual(
                first["identities"]["routes"],
                ["R1"],
            )
            self.assertEqual(
                first["identities"][
                    "service_ids_in_trips"
                ],
                ["WK"],
            )

    def test_feed_info_and_temporal_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed = Path(tmp) / "feed.zip"
            write_zip(feed, self.fixture_files())

            manifest, _ = self.run_observe(feed)

            self.assertEqual(
                manifest["feed_info"][0][
                    "feed_start_date"
                ],
                "20260824",
            )
            self.assertEqual(
                manifest["feed_info"][0][
                    "feed_end_date"
                ],
                "20260905",
            )

            self.assertEqual(
                manifest["calendar"]["start_date"][
                    "minimum"
                ],
                "20260824",
            )
            self.assertEqual(
                manifest["calendar"]["end_date"][
                    "maximum"
                ],
                "20260904",
            )

            self.assertEqual(
                manifest["calendar_dates"]["date"][
                    "minimum"
                ],
                "20260831",
            )
            self.assertEqual(
                manifest["calendar_dates"]["date"][
                    "maximum"
                ],
                "20260905",
            )

            self.assertEqual(
                manifest["calendar_dates"][
                    "exception_types"
                ],
                ["1", "2"],
            )


if __name__ == "__main__":
    unittest.main()
