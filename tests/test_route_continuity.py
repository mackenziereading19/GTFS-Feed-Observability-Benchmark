import unittest

from src.route_continuity import (
    classify,
    core_signature,
    full_signature,
    group_by_signature,
)


class RouteContinuityTest(unittest.TestCase):

    def test_full_signature_ignores_route_id(self):
        fields = (
            "route_id",
            "agency_id",
            "route_short_name",
            "route_long_name",
            "route_type",
        )

        old = {
            "route_id": "OLD",
            "agency_id": "A",
            "route_short_name": "10",
            "route_long_name": "Town - Station",
            "route_type": "3",
        }

        new = dict(old)
        new["route_id"] = "NEW"

        self.assertEqual(
            full_signature(old, fields),
            full_signature(new, fields),
        )

    def test_core_signature_ignores_non_core_change(self):
        old = {
            "route_id": "OLD",
            "agency_id": "A",
            "route_short_name": "10",
            "route_long_name": "Town - Station",
            "route_type": "3",
            "route_color": "FFFFFF",
        }

        new = dict(old)
        new["route_id"] = "NEW"
        new["route_color"] = "000000"

        self.assertEqual(
            core_signature(old),
            core_signature(new),
        )

    def test_one_to_one_id_regeneration(self):
        old_rows = [
            {
                "route_id": "OLD",
                "agency_id": "A",
                "route_short_name": "10",
                "route_long_name": "Town - Station",
                "route_type": "3",
            }
        ]

        new_rows = [
            {
                "route_id": "NEW",
                "agency_id": "A",
                "route_short_name": "10",
                "route_long_name": "Town - Station",
                "route_type": "3",
            }
        ]

        old_groups = group_by_signature(
            old_rows,
            core_signature,
        )

        new_groups = group_by_signature(
            new_rows,
            core_signature,
        )

        result = classify(
            old_groups,
            new_groups,
        )

        self.assertEqual(
            result["one_to_one"],
            [
                {
                    "old_ids": ["OLD"],
                    "new_ids": ["NEW"],
                }
            ],
        )

        self.assertEqual(
            result["unmatched_old_ids"],
            [],
        )

        self.assertEqual(
            result["unmatched_new_ids"],
            [],
        )

    def test_ambiguous_duplicate_signature(self):
        old_rows = [
            {
                "route_id": "OLD1",
                "agency_id": "A",
                "route_short_name": "10",
                "route_long_name": "Town - Station",
                "route_type": "3",
            },
            {
                "route_id": "OLD2",
                "agency_id": "A",
                "route_short_name": "10",
                "route_long_name": "Town - Station",
                "route_type": "3",
            },
        ]

        new_rows = [
            {
                "route_id": "NEW",
                "agency_id": "A",
                "route_short_name": "10",
                "route_long_name": "Town - Station",
                "route_type": "3",
            }
        ]

        result = classify(
            group_by_signature(
                old_rows,
                core_signature,
            ),
            group_by_signature(
                new_rows,
                core_signature,
            ),
        )

        self.assertEqual(
            result["one_to_one"],
            [],
        )

        self.assertEqual(
            len(result["ambiguous"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
