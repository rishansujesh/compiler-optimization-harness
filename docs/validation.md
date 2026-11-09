# Validation record

Validated locally on Linux with Python 3.12.14 and GCC 14.2.0 on 2026-11-09:

- 26 pytest cases passed: deterministic search, invalid settings, checksum and timing rejection, median/MAD calculation, shell argument preservation, process-group timeout cleanup, memory/output limits, real compilation and reports, independent mathematical workload checks, and suppression of miscompiled candidates.
- Ruff lint and formatting checks passed.
- Wheel and source distribution built successfully.
- Installed the wheel into a fresh virtual environment outside the repository and ran all three bundled workloads successfully.
- An eight-configuration, seven-sample experiment across all three workloads passed every candidate's correctness checks; [raw results](measurements/cloud-gcc14/README.md) are retained.

The initial [GitHub Actions run](https://github.com/rishansujesh/compiler-optimization-harness/actions/runs/42703744174) passed the Python 3.11, 3.12 and 3.13 test/build/install jobs and the GCC and Clang smoke jobs. Every curated smoke configuration passed its correctness checks.
