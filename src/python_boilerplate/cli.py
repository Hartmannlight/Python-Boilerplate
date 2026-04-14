from __future__ import annotations

import argparse

from python_boilerplate.app import create_worker_service
from python_boilerplate.config import load_settings
from python_boilerplate.runtime import check_health, emit_health_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="boilerplate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="Run the worker service.")
    subparsers.add_parser("health", help="Check service health via the metrics endpoint.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()

    if args.command == "run":
        return create_worker_service().run()

    if args.command == "health":
        return emit_health_report(check_health(settings))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
