"""Compile in parallel, then correctness-check and measure serially."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import shutil
import statistics
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from .process import Limits, run
from .search import configurations

WORKLOADS = ("gemm", "fft", "ray")


def observation(result, expected: float | None = None) -> tuple[float, float]:
    if result.timed_out or result.returncode:
        raise ValueError(f"process failed: exit={result.returncode}, timeout={result.timed_out}")
    try:
        data = json.loads(result.stdout)
        checksum, seconds = float(data["checksum"]), float(data["seconds"])
    except (ValueError, TypeError, KeyError) as error:
        raise ValueError("workload did not emit a valid observation") from error
    if not math.isfinite(checksum) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("nonfinite checksum or nonpositive timing")
    if expected is not None and not math.isclose(checksum, expected, rel_tol=1e-8, abs_tol=1e-6):
        raise ValueError(f"checksum mismatch: {checksum} != {expected}")
    return checksum, seconds


def summarize(samples: list[float]) -> dict:
    median = statistics.median(samples)
    mad = statistics.median(abs(value - median) for value in samples)
    return {
        "median_seconds": median,
        "mad_seconds": mad,
        "relative_mad": mad / median,
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }


def experiment(
    *,
    compiler: str = "gcc",
    budget: int = 12,
    seed: int = 42,
    runs: int = 7,
    warmups: int = 2,
    jobs: int = 2,
    target_seconds: float = 0.05,
    limits: Limits | None = None,
    workloads: tuple[str, ...] = WORKLOADS,
    cpu: int | None = None,
) -> dict:
    limits = limits or Limits()
    if runs < 3 or warmups < 1 or jobs < 1:
        raise ValueError("runs >= 3, warmups >= 1 and jobs >= 1 are required")
    if not math.isfinite(target_seconds) or not 0.001 <= target_seconds <= 10:
        raise ValueError("target seconds must be between 0.001 and 10")
    if not workloads or len(set(workloads)) != len(workloads) or set(workloads) - set(WORKLOADS):
        raise ValueError("choose distinct bundled workloads: gemm, fft, ray")
    executable = shutil.which(compiler)
    if executable is None:
        raise ValueError(f"compiler not found: {compiler}")
    version_result = run([executable, "--version"], limits)
    if version_result.returncode or version_result.timed_out:
        raise ValueError("could not query compiler version")
    version = version_result.stdout
    family = (
        "clang"
        if "clang" in version.lower()
        else "gcc"
        if any(word in version.lower() for word in ("gcc", "free software foundation"))
        else None
    )
    if family is None:
        raise ValueError("only GCC and Clang are supported")
    candidates = configurations(family, budget, seed)
    original_affinity = os.sched_getaffinity(0)
    if cpu is not None and cpu not in original_affinity:
        raise ValueError(f"CPU {cpu} is outside allowed affinity {sorted(original_affinity)}")
    report = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "compiler": executable,
            "compiler_version": version.strip(),
            "cpu_count": os.cpu_count(),
            "cpu_model": _cpu_model(),
            "allowed_cpus": sorted(original_affinity),
        },
        "settings": {
            "budget": budget,
            "seed": seed,
            "runs": runs,
            "warmups": warmups,
            "compile_jobs": jobs,
            "target_seconds": target_seconds,
            "cpu": cpu,
            "limits": {
                "timeout": limits.timeout,
                "memory_mb": limits.memory_mb,
                "file_mb": limits.file_mb,
            },
        },
        "workloads": [],
    }
    with tempfile.TemporaryDirectory(prefix="opt-harness-") as temporary:
        build = Path(temporary)
        sources = Path(__file__).with_name("workloads")
        tasks = []
        for name in workloads:
            for index, flags in enumerate([("-O0",), *candidates]):
                tasks.append((name, index, flags))

        def compile_one(task):
            name, index, flags = task
            binary = build / f"{name}-{index}"
            command = [
                executable,
                "-std=c11",
                "-D_POSIX_C_SOURCE=200809L",
                *flags,
                str(sources / f"{name}.c"),
                "-lm",
                "-o",
                str(binary),
            ]
            result = run(command, limits)
            return (name, index), (binary, result)

        # No timing runs overlap compiler processes.
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            compiled = dict(pool.map(compile_one, tasks))
        try:
            if cpu is not None:
                os.sched_setaffinity(0, {cpu})
            for name in workloads:
                entry = {
                    "name": name,
                    "source_sha256": hashlib.sha256(
                        (sources / f"{name}.c").read_bytes()
                    ).hexdigest(),
                    "configurations": [],
                }
                report["workloads"].append(entry)
                try:
                    baseline_binary, baseline_compile = compiled[name, 1]
                    reference_binary, reference_compile = compiled[name, 0]
                    if any(
                        r.returncode or r.timed_out for r in (baseline_compile, reference_compile)
                    ):
                        raise ValueError("baseline or reference compilation failed")
                    _, first = observation(run([str(baseline_binary), "1"], limits))
                    repeat = max(1, min(100000, math.ceil(target_seconds / first)))
                    expected, _ = observation(run([str(reference_binary), str(repeat)], limits))
                    entry.update(repetitions=repeat, reference_checksum=expected)
                except ValueError as error:
                    entry["error"] = str(error)
                    entry["baseline_compile"] = baseline_compile.to_dict()
                    entry["reference_compile"] = reference_compile.to_dict()
                    continue
                active = []
                for index, flags in enumerate(candidates, 1):
                    binary, result = compiled[name, index]
                    record = {
                        "id": index - 1,
                        "flags": list(flags),
                        "status": "ok",
                        "compile": result.to_dict(),
                        "samples_seconds": [],
                    }
                    entry["configurations"].append(record)
                    if result.returncode or result.timed_out:
                        record.update(status="compile_failed")
                        continue
                    try:
                        for _ in range(warmups):
                            observation(run([str(binary), str(repeat)], limits), expected)
                        active.append((binary, record))
                    except ValueError as error:
                        record.update(status="validation_failed", error=str(error))
                rng = random.Random(seed)
                for _ in range(runs):
                    rng.shuffle(active)
                    for binary, record in active:
                        if record["status"] != "ok":
                            continue
                        result = run([str(binary), str(repeat)], limits)
                        try:
                            _, seconds = observation(result, expected)
                            record["samples_seconds"].append(seconds)
                        except ValueError as error:
                            record.update(
                                status="run_failed", error=str(error), failed_run=result.to_dict()
                            )
                for record in entry["configurations"]:
                    if record["status"] == "ok":
                        record.update(summarize(record["samples_seconds"]))
                baseline = entry["configurations"][0]
                if baseline["status"] == "ok":
                    for record in entry["configurations"]:
                        if record["status"] == "ok":
                            record["speedup_vs_O2"] = (
                                baseline["median_seconds"] / record["median_seconds"]
                            )
                else:
                    entry["error"] = (
                        "baseline validation or measurement failed; no speedups reported"
                    )
        finally:
            os.sched_setaffinity(0, original_affinity)
    return report


def _cpu_model() -> str:
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor()
