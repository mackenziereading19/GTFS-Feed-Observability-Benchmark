"""Unified command-line entry point for GTFS observability tools."""

import sys

from . import (
    gtfs_compare,
    gtfs_observe,
    route_continuity,
    route_forensics,
    service_continuity,
)


COMMANDS = {
    "observe": gtfs_observe.main,
    "compare": gtfs_compare.main,
    "route-continuity": route_continuity.main,
    "route-forensics": route_forensics.main,
    "service-continuity": service_continuity.main,
}


def print_help(file=sys.stdout):
    file.write(
        "usage: python3 -m src.cli COMMAND [ARGS...]\n"
        "\n"
        "GTFS feed observability tools.\n"
        "\n"
        "commands:\n"
        "  observe             Create a deterministic feed manifest.\n"
        "  compare             Compare two observability manifests.\n"
        "  route-continuity    Analyse route semantic continuity.\n"
        "  route-forensics     Inspect unmatched route continuity.\n"
        "  service-continuity  Analyse service-calendar continuity.\n"
        "\n"
        "Run COMMAND --help for command-specific help.\n"
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"-h", "--help"}:
        print_help()
        return 0

    command = argv[0]

    if command not in COMMANDS:
        print(
            f"Unknown command: {command}",
            file=sys.stderr,
        )
        print_help(file=sys.stderr)
        return 2

    return COMMANDS[command](
        argv[1:],
        prog=f"python3 -m src.cli {command}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
