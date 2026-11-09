"""Machine-readable samples and concise human-readable comparisons."""
import csv
import json
from pathlib import Path


def write_report(report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    (output / "results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    fields = ["workload", "id", "status", "flags", "median_seconds", "mad_seconds", "speedup_vs_O2"]
    lines = ["# Compiler optimization experiment", "",
             f"Compiler: `{report['environment']['compiler_version'].splitlines()[0]}`", "",
             "Timings are serial, warmed, randomized by round, and checksum-validated against -O0.",
             "Speedups are exploratory observations, not statistical significance claims.", "",
             "| Workload | ID | Median (ms) | MAD (ms) | Speedup vs -O2 | Flags |",
             "|---|---:|---:|---:|---:|---|"]
    with (output / "results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for workload in report["workloads"]:
            if "error" in workload:
                lines.append(f"\n{workload['name']}: {workload['error']}\n")
            for record in workload["configurations"]:
                row = {key: record.get(key, "") for key in fields}
                row.update(workload=workload["name"], flags=" ".join(record["flags"]))
                writer.writerow(row)
                if record["status"] == "ok":
                    speedup = record.get("speedup_vs_O2")
                    ratio = f"{speedup:.3f}x" if speedup is not None else "N/A"
                    lines.append(f"| {workload['name']} | {record['id']} | "
                                 f"{record['median_seconds'] * 1000:.3f} | "
                                 f"{record['mad_seconds'] * 1000:.3f} | {ratio} | `{row['flags']}` |")
                else:
                    lines.append(f"| {workload['name']} | {record['id']} | "
                                 f"{record['status']} | — | — | `{row['flags']}` |")
    (output / "report.md").write_text("\n".join(lines) + "\n")
