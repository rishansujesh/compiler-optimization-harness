# Compiler Optimization Harness

[![CI](https://github.com/rishansujesh/compiler-optimization-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/rishansujesh/compiler-optimization-harness/actions/workflows/ci.yml)

A Linux command-line tool for exploring GCC and Clang flags on three compute-bound C workloads. Every measured run must match an unoptimized reference checksum. Compilation is parallel; measurement is serial, warmed, and randomized across configurations.

## Quick start

Requires Linux, Python 3.11+, and GCC or Clang. The runtime uses only Python's standard library.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
opt-harness --compiler gcc --budget 12 --runs 7 --output results/gcc-first
cat results/gcc-first/report.md
```

The output directory must be new. Each experiment produces raw samples and metadata in `results.json`, a flat `results.csv`, and a Markdown comparison. Exit codes: `0` completed with usable baselines (individual candidate failures remain in reports), `1` a workload baseline failed, `2` invalid input or infrastructure failure.

```sh
# Clang, reproducible search, bounded compiler parallelism
opt-harness --compiler clang --seed 42 --jobs 2 --budget 20 --output results/clang-first
# Pin measurement to an allowed CPU (check `taskset -pc $$` first)
opt-harness --workloads gemm --cpu 2 --target-seconds 0.1 --output results/pinned
pytest
ruff check .
ruff format --check .
python -m build
```

## What is implemented

- Deterministic random search: 25 whitelisted GCC flags across 11 mutually exclusive categories; a smaller Clang-specific subset. The budget includes the `-O2` baseline. No arbitrary flags, shell strings, fast-math, or architecture-specific instructions.
- Naive 128×128 GEMM, iterative radix-2 FFT, and Möller–Trumbore ray/triangle intersection. Data varies between repetitions and contributes to printed checksums to keep work observable.
- Parallel isolated compiler processes, each with wall-clock, CPU, address-space and output-file limits. Entire process groups are killed on timeout and cleaned up on normal exit.
- An `-O0` reference, candidate warmups, checksum validation on **every** timed invocation, calibrated repetition counts, randomized measurement rounds, median and median absolute deviation (MAD).
- Compiler version, CPU model, affinity, source hashes, seed, flags, commands, failures, and all timing samples in the report.

## Interpreting results

Speedup is the `-O2` median divided by a candidate's median for the same workload. A value above 1 is faster in this experiment. MAD quantifies dispersion, **not** confidence. Repeat apparent gains on a quiet machine and a held-out seed before drawing conclusions. The best of many noisy trials is biased upward.

The workloads time their own kernel regions with `CLOCK_MONOTONIC`; Python launch and process polling are excluded. Calibration targets 50 ms by default, but the cap of 100,000 repetitions and system noise mean this is not a guaranteed duration. All configurations for a workload use the same repetition count. Default limits apply per subprocess, so `--jobs` multiplies the possible memory budget. See [methodology](docs/methodology.md) and [architecture](docs/architecture.md).

## Scope and limitations

This is a controlled experiment tool, not a general autotuner or a sandbox for hostile code. It only runs bundled sources, but the selected compiler is executable code. Resource limits are per process and process groups cannot contain a malicious program that deliberately escapes its session; use a container/VM for untrusted tools. Linux is currently required. Checksums catch many miscompilations, but they are not a proof of algorithm correctness. There is no claim of stable performance superiority across CPUs or compiler versions.

Version 0.1.0 is an initial tested implementation. See [contribution guidelines](CONTRIBUTING.md) and the MIT [license](LICENSE).

Local test evidence and unexecuted platform checks are listed in the [validation record](docs/validation.md).
