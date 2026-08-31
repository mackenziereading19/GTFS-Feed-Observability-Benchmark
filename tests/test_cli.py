import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTest(unittest.TestCase):
    def run_command(self, *args):
        return subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_top_level_help(self):
        result = self.run_command(
            sys.executable,
            "-m",
            "src.cli",
            "--help",
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "GTFS feed observability tools.",
            result.stdout,
        )

        for command in (
            "observe",
            "compare",
            "route-continuity",
            "route-forensics",
            "service-continuity",
        ):
            self.assertIn(command, result.stdout)

    def test_unknown_command(self):
        result = self.run_command(
            sys.executable,
            "-m",
            "src.cli",
            "not-a-command",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "Unknown command: not-a-command",
            result.stderr,
        )

    def test_subcommand_help_matches_existing_script(self):
        pairs = (
            ("observe", "src/gtfs_observe.py"),
            ("compare", "src/gtfs_compare.py"),
            (
                "route-continuity",
                "src/route_continuity.py",
            ),
            (
                "route-forensics",
                "src/route_forensics.py",
            ),
            (
                "service-continuity",
                "src/service_continuity.py",
            ),
        )

        for command, script in pairs:
            with self.subTest(command=command):
                direct = self.run_command(
                    sys.executable,
                    script,
                    "--help",
                )

                unified = self.run_command(
                    sys.executable,
                    "-m",
                    "src.cli",
                    command,
                    "--help",
                )

                self.assertEqual(
                    direct.returncode,
                    unified.returncode,
                )

                direct_lines = direct.stdout.splitlines()
                unified_lines = unified.stdout.splitlines()

                self.assertTrue(
                    direct_lines[0].startswith("usage: ")
                )

                self.assertTrue(
                    unified_lines[0].startswith(
                        f"usage: python3 -m src.cli {command}"
                    )
                )

                self.assertEqual(
                    direct_lines[1:],
                    unified_lines[1:],
                )

                self.assertEqual(
                    direct.stderr,
                    unified.stderr,
                )

    def test_observe_output_matches_existing_script(self):
        feed = (
            ROOT
            / "tmp"
            / "mbta-evaluation"
            / "20260623.zip"
        )

        self.assertTrue(feed.is_file())

        direct = self.run_command(
            sys.executable,
            "src/gtfs_observe.py",
            str(feed),
        )

        unified = self.run_command(
            sys.executable,
            "-m",
            "src.cli",
            "observe",
            str(feed),
        )

        self.assertEqual(direct.returncode, 0)
        self.assertEqual(unified.returncode, 0)
        self.assertEqual(direct.stdout, unified.stdout)
        self.assertEqual(direct.stderr, unified.stderr)

    def test_pairwise_outputs_match_existing_scripts(self):
        old_feed = (
            ROOT
            / "tmp"
            / "mbta-evaluation"
            / "20260623.zip"
        )

        new_feed = (
            ROOT
            / "tmp"
            / "mbta-evaluation"
            / "20260624.zip"
        )

        pairs = (
            (
                "route-continuity",
                "src/route_continuity.py",
            ),
            (
                "service-continuity",
                "src/service_continuity.py",
            ),
        )

        for command, script in pairs:
            with self.subTest(command=command):
                direct = self.run_command(
                    sys.executable,
                    script,
                    str(old_feed),
                    str(new_feed),
                )

                unified = self.run_command(
                    sys.executable,
                    "-m",
                    "src.cli",
                    command,
                    str(old_feed),
                    str(new_feed),
                )

                self.assertEqual(
                    direct.returncode,
                    unified.returncode,
                )

                self.assertEqual(
                    direct.stdout,
                    unified.stdout,
                )

                self.assertEqual(
                    direct.stderr,
                    unified.stderr,
                )


if __name__ == "__main__":
    unittest.main()
