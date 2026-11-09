# Validation record

Validated locally on Linux with Python 3.12.14 and GCC 14.2.0 on 2026-11-09:

- 26 pytest cases passed: deterministic search, invalid settings, checksum and timing rejection, median/MAD calculation, shell argument preservation, process-group timeout cleanup, memory/output limits, real compilation and reports, independent mathematical workload checks, and suppression of miscompiled candidates.
- Ruff lint and formatting checks passed.
- Wheel and source distribution built successfully.
- Installed the wheel into a fresh virtual environment outside the repository and ran all three bundled workloads successfully.
- An eight-configuration, seven-sample experiment across all three workloads passed every candidate's correctness checks; [raw results](measurements/cloud-gcc14/README.md) are retained.

Clang and Python 3.11/3.13 are covered by the configured GitHub Actions matrix but were not available for local execution. GitHub-hosted CI has not been run because repository creation was denied by the connected integration. This record distinguishes local checks from configured future CI checks.
