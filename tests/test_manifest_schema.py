import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "manifest-v2.schema.json"
MANIFEST_DIR = ROOT / "examples" / "manifests"


class ManifestSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SCHEMA_PATH.open(encoding="utf-8") as f:
            cls.schema = json.load(f)

        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

        manifest_path = sorted(MANIFEST_DIR.glob("*.json"))[0]
        with manifest_path.open(encoding="utf-8") as f:
            cls.example = json.load(f)

    def assertInvalid(self, instance):
        with self.assertRaises(ValidationError):
            self.validator.validate(instance)

    def test_tracked_example_manifests_validate(self):
        manifests = sorted(MANIFEST_DIR.glob("*.json"))

        self.assertGreater(len(manifests), 0)

        for path in manifests:
            with self.subTest(path=path.name):
                with path.open(encoding="utf-8") as f:
                    manifest = json.load(f)

                self.validator.validate(manifest)

    def test_nullable_optional_source_sections_validate(self):
        manifest = copy.deepcopy(self.example)

        manifest["feed_info"] = None
        manifest["calendar"] = None
        manifest["calendar_dates"] = None

        self.validator.validate(manifest)

    def test_wrong_schema_version_fails(self):
        manifest = copy.deepcopy(self.example)
        manifest["schema_version"] = 3

        self.assertInvalid(manifest)

    def test_malformed_sha256_fails(self):
        manifest = copy.deepcopy(self.example)
        manifest["source"]["sha256"] = "not-a-sha256"

        self.assertInvalid(manifest)

    def test_negative_table_row_count_fails(self):
        manifest = copy.deepcopy(self.example)

        table = next(iter(manifest["tables"]))
        manifest["tables"][table]["rows"] = -1

        self.assertInvalid(manifest)

    def test_null_table_row_count_is_allowed(self):
        manifest = copy.deepcopy(self.example)

        table = next(iter(manifest["tables"]))
        manifest["tables"][table]["rows"] = None

        self.validator.validate(manifest)

    def test_missing_required_top_level_key_fails(self):
        manifest = copy.deepcopy(self.example)
        del manifest["source"]

        self.assertInvalid(manifest)


if __name__ == "__main__":
    unittest.main()
