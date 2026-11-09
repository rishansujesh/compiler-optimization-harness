import json
import math
import os
import shutil
import sys

import pytest

from opt_harness.cli import main
from opt_harness.experiment import experiment, observation, summarize
from opt_harness.process import Limits, ProcessResult, run
from opt_harness.report import write_report
from opt_harness.search import BASELINE, GCC_GROUPS, configurations


def result(checksum=12, seconds=0.1, code=0, timeout=False):
    return ProcessResult(
        [], code, 0.2, json.dumps(dict(checksum=checksum, seconds=seconds)), "", timeout
    )


def test_seeded_search_has_one_flag_per_category():
    values = configurations("gcc", 100, 42)
    assert values == configurations("gcc", 100, 42)
    assert values != configurations("gcc", 100, 43)
    assert len(set(values)) == 100
    assert values[0] == BASELINE
    for flags in values:
        for group in GCC_GROUPS:
            assert len(set(flags) & set(group)) <= 1
        assert set(flags) <= {flag for group in GCC_GROUPS for flag in group}


@pytest.mark.parametrize("budget", [0, -1, 1001])
def test_bad_budget(budget):
    with pytest.raises(ValueError):
        configurations("gcc", budget, 1)


@pytest.mark.parametrize(
    "sample",
    [
        result(checksum=math.nan),
        result(seconds=0),
        result(checksum=13),
        result(code=1),
        result(timeout=True),
    ],
)
def test_invalid_observation(sample):
    with pytest.raises(ValueError):
        observation(sample, 12)


def test_median_and_mad_resist_outlier():
    stats = summarize([1, 1, 2, 2, 100])
    assert stats["median_seconds"] == 2
    assert stats["mad_seconds"] == 1


def test_no_shell_interpolation(tmp_path):
    marker = tmp_path / "unexpected"
    command = f"$(touch {marker})"
    outcome = run([sys.executable, "-c", "import sys; print(sys.argv[1])", command], Limits())
    assert outcome.returncode == 0
    assert outcome.stdout.strip() == command
    assert not marker.exists()


def test_timeout_kills_descendant(tmp_path):
    marker = tmp_path / "orphan"
    child_code = (
        f"import time; from pathlib import Path; time.sleep(1); Path({str(marker)!r}).touch()"
    )
    code = (
        f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
        "time.sleep(30)"
    )
    outcome = run([sys.executable, "-c", code], Limits(timeout=0.3))
    assert outcome.timed_out
    assert outcome.elapsed_seconds < 3
    # A second subprocess provides a bounded wait beyond the descendant deadline.
    run([sys.executable, "-c", "import time; time.sleep(1.1)"], Limits())
    assert not marker.exists()


def test_memory_limit():
    outcome = run([sys.executable, "-c", "x = bytearray(256 * 1024 * 1024)"], Limits(memory_mb=64))
    assert outcome.returncode != 0
    assert "MemoryError" in outcome.stderr


def test_output_is_bounded():
    outcome = run(
        [sys.executable, "-c", "import os; os.write(1, b'x' * (2**21))"], Limits(file_mb=1)
    )
    assert len(outcome.stdout) <= 65536


@pytest.mark.parametrize("timeout", [0, -1, math.inf, math.nan])
def test_bad_limits(timeout):
    with pytest.raises(ValueError):
        Limits(timeout=timeout)


@pytest.mark.skipif(shutil.which("gcc") is None, reason="GCC unavailable")
def test_real_experiment_and_reports(tmp_path):
    affinity = os.sched_getaffinity(0)
    report = experiment(
        budget=2, runs=3, warmups=1, jobs=2, target_seconds=0.003, cpu=min(affinity)
    )
    assert os.sched_getaffinity(0) == affinity
    for workload in report["workloads"]:
        assert "error" not in workload
        assert len(workload["source_sha256"]) == 64
        for record in workload["configurations"]:
            assert record["status"] == "ok", record
            assert len(record["samples_seconds"]) == 3
            assert record["speedup_vs_O2"] > 0
    output = tmp_path / "report"
    write_report(report, output)
    assert json.loads((output / "results.json").read_text())["schema_version"] == 1
    assert "Speedup" in (output / "report.md").read_text()
    assert len((output / "results.csv").read_text().splitlines()) == 7
    with pytest.raises(FileExistsError):
        write_report(report, output)


def test_cli_rejects_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["opt-harness", "--output", str(tmp_path)])
    assert main() == 2


def test_compile_failure_is_reported(tmp_path):
    wrapper = tmp_path / "gcc-wrapper"
    wrapper.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo gcc; exit 0; fi\nexit 1\n')
    wrapper.chmod(0o755)
    report = experiment(compiler=str(wrapper), budget=1, runs=3, workloads=("gemm",))
    assert report["workloads"][0]["error"] == "baseline or reference compilation failed"


def test_invalid_workload_and_compiler():
    with pytest.raises(ValueError):
        experiment(workloads=("oops",))
    with pytest.raises(ValueError):
        experiment(compiler="missing-compiler-12345")


@pytest.mark.skipif(shutil.which("gcc") is None, reason="GCC unavailable")
@pytest.mark.parametrize("workload", ["gemm", "fft", "ray"])
def test_workload_against_independent_math(tmp_path, workload):
    from pathlib import Path

    import opt_harness

    source = Path(opt_harness.__file__).parent / "workloads" / f"{workload}.c"
    binary = tmp_path / workload
    compiled = run(
        [
            "gcc",
            "-O2",
            "-std=c11",
            "-D_POSIX_C_SOURCE=200809L",
            str(source),
            "-lm",
            "-o",
            str(binary),
        ],
        Limits(),
    )
    assert compiled.returncode == 0
    actual, _ = observation(run([str(binary), "1"], Limits()))
    if workload == "fft":
        # Parseval: sum |FFT(x)|² = N sum |x|² for this unnormalized transform.
        expected = 4096 * sum(math.sin(i * 0.013) ** 2 for i in range(4096))
    elif workload == "gemm":
        # Sum(A B) = sum_k column_sum(A,k) * row_sum(B,k).
        expected = 0
        for k in range(128):
            a_sum = sum(((i + k) % 17) / 17 for i in range(128))
            b_sum = sum(((k * 3 + j) % 13) / 13 for j in range(128))
            expected += a_sum * b_sum
    else:
        # Intersection with z=0 from z=-1 has t=1. Test the projected point
        # against the unit right triangle; no cross-product code is reused.
        expected = sum((i % 997) / 997 + 0.01 + (i % 991) / 991 + 0.02 <= 1 for i in range(200000))
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-6)


def test_miscompiled_candidate_never_gets_a_speedup(monkeypatch):
    import importlib

    module = importlib.import_module("opt_harness.experiment")

    def fake_run(argv, limits):
        if argv[-1] == "--version":
            return ProcessResult(argv, 0, 0.01, "gcc test compiler", "", False)
        if "-o" in argv:
            return ProcessResult(argv, 0, 0.01, "", "", False)
        return result(checksum=99 if argv[0].endswith("gemm-2") else 12)

    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(module.shutil, "which", lambda _: "/fake/gcc")
    report = module.experiment(budget=2, runs=3, warmups=1, workloads=("gemm",))
    baseline, bad = report["workloads"][0]["configurations"]
    assert baseline["speedup_vs_O2"] == 1
    assert bad["status"] == "validation_failed"
    assert bad["samples_seconds"] == []
    assert "speedup_vs_O2" not in bad
