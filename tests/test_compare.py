import json
import unittest
from pathlib import Path

from src.gtfs_compare import (
    compare_manifests,
)


ROOT = Path(__file__).resolve().parents[1]


class CompareManifestTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(
            (
                ROOT
                / "examples"
                / "manifests"
                / "mdb-1132.json"
            ).read_text()
        )

        cls.changed = json.loads(
            (
                ROOT
                / "examples"
                / "manifests"
                / "mdb-1132-controlled-v1.json"
            ).read_text()
        )

        cls.result = compare_manifests(
            cls.baseline,
            cls.changed,
        )

    def test_source_hash_changes(self):
        self.assertTrue(
            self.result["source_changed"]
        )

    def test_transfers_removed(self):
        self.assertEqual(
            self.result["tables"]["removed"],
            ["transfers.txt"],
        )

        self.assertEqual(
            self.result["tables"]["added"],
            [],
        )

    def test_expected_table_row_changes(self):
        changes = self.result["tables"]["row_changes"]

        self.assertEqual(
            set(changes),
            {
                "calendar_dates.txt",
                "stops.txt",
            },
        )

        self.assertEqual(
            changes["stops.txt"]["delta"],
            1,
        )

        self.assertEqual(
            changes["calendar_dates.txt"]["delta"],
            1,
        )

    def test_stop_entity_delta(self):
        stops = self.result["entities"]["stops"]

        self.assertEqual(
            stops["rows"]["delta"],
            1,
        )

        self.assertEqual(
            stops["unique_ids"]["delta"],
            1,
        )

    def test_stop_identity_added(self):
        identities = self.result["identities"]

        self.assertEqual(
            identities["stops"]["added"],
            ["__OBSERVABILITY_SYNTHETIC_STOP__"],
        )

        self.assertEqual(
            identities["stops"]["removed"],
            [],
        )

    def test_feed_end_date_change(self):
        self.assertEqual(
            self.result["feed_info"]["feed_end_date"],
            {
                "before": "20260926",
                "after": "20261003",
            },
        )

    def test_temporal_bound_changes(self):
        self.assertEqual(
            self.result["temporal_bounds"],
            {
                "calendar.end_date.maximum": {
                    "before": "20261031",
                    "after": "20261107",
                },
                "calendar_dates.date.maximum": {
                    "before": "20260926",
                    "after": "20261003",
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
