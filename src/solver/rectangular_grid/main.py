"""Run the tiny-instance oracle and write solutions plus a diagnostic report."""

import argparse
import json
from pathlib import Path

from cgshop2027_pyutils.io import read_instance
from cgshop2027_pyutils.verify import check_for_errors

from solver import solve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output directory")
    parser.add_argument("--instances", type=Path, default=Path(__file__).parent / "examples",
                        help="One instance JSON file or a directory of *.instance.json files")
    parser.add_argument("--time-limit", type=float, default=50.0)
    parser.add_argument("--max-positions", type=int, default=20)
    parser.add_argument("--max-cells", type=int, default=36)
    args = parser.parse_args()
    if not args.instances.exists():
        parser.error(f"Input does not exist: {args.instances}")
    paths = [args.instances] if args.instances.is_file() else sorted(args.instances.glob("*.instance.json"))
    if not paths:
        parser.error("No *.instance.json files found")
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    failed = False
    for path in paths:
        # File stems, rather than arbitrary instance UIDs, determine output paths.
        stem = path.name.removesuffix(".instance.json").removesuffix(".json")
        destination = args.output / f"{stem}.solution.json"
        # Do not let a previous successful run masquerade as this run's result.
        destination.unlink(missing_ok=True)
        try:
            instance = read_instance(path)
            result = solve(instance, time_limit=args.time_limit,
                           max_positions=args.max_positions, max_cells=args.max_cells)
            report = {"input": str(path), "instance_uid": instance.instance_uid, **result.report()}
            if result.solution is not None:
                errors = check_for_errors(instance, result.solution)
                if errors:
                    raise RuntimeError(f"Competition verification failed: {errors}")
                destination.write_text(result.solution.model_dump_json(indent=2) + "\n")
                report["solution_file"] = str(destination)
            else:
                failed = True
        except (ValueError, OSError) as error:
            failed = True
            report = {"input": str(path), "status": "REJECTED", "proved_optimal": False,
                      "error": str(error)}
        reports.append(report)
        print(json.dumps(report))
    (args.output / "report.json").write_text(json.dumps(reports, indent=2) + "\n")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
