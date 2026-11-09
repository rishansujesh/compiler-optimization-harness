import argparse
import sys
from pathlib import Path

from .experiment import WORKLOADS, experiment
from .process import Limits
from .report import write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Correctness-gated GCC/Clang flag experiments (Linux)")
    parser.add_argument("--compiler", default="gcc")
    parser.add_argument("--budget", type=int, default=12, help="configurations including -O2 baseline")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--jobs", type=int, default=2, help="parallel compiler processes; timing is serial")
    parser.add_argument("--target-seconds", type=float, default=0.05)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--memory-mb", type=int, default=1024)
    parser.add_argument("--cpu", type=int, help="pin timing processes to an allowed logical CPU")
    parser.add_argument("--workloads", nargs="+", choices=WORKLOADS, default=list(WORKLOADS))
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output directory already exists; choose a new path")
        report = experiment(compiler=args.compiler, budget=args.budget, seed=args.seed,
                            runs=args.runs, warmups=args.warmups, jobs=args.jobs,
                            target_seconds=args.target_seconds,
                            limits=Limits(args.timeout, args.memory_mb),
                            workloads=tuple(args.workloads), cpu=args.cpu)
        write_report(report, args.output)
        print(f"Report: {(args.output / 'report.md').resolve()}")
        return 1 if any("error" in workload for workload in report["workloads"]) else 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"opt-harness: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
